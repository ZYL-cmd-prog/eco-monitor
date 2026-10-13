# -*- coding: utf-8 -*-
"""
transformer.py — 文档 2.3 的未来生态环境质量预测模型（Transformer）

架构（对应申报书 2.3「编码器 Encoder + 回归器 Regressor」）：
  - 输入：过去 T=50 期 × C 个指标的滑动窗口 → C×T 个输入通道。
      文档全量目标 1048 ≈ 21 指标 × 50 步；当前用真实可得的 MODIS 长期
      NDVI/EVI（2000 年至今，约 300 个月点），即 2 × 50 = 100 通道。
  - 编码器：n_layers 层 TransformerEncoder（多头自注意力 + 前馈网络）。
  - 回归器：编码输出均值池化 + MLP → 未来 horizon=12 期（文档「12 输出通道」）。
  - 置信区间：验证集残差标准差 × 1.96（与 baseline.py 一致）。

训练：CPU 小模型（d_model=32 / 2 层 / 2 头，约几万参数），约 300 点数据秒级
收敛；GitHub Actions 每周重训。torch 不可用或历史点不足时跳过（保留 baseline
的 prediction.json 不动）。

用法：
    python transformer.py               # 训练并写 prediction.json
    python transformer.py --check       # 仅 numpy 数据检查（无需 torch），打印形状
输出：eco-monitor/public/data/prediction.json（多指标 series 格式）
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

# Windows 控制台 GBK 编码下打印中文/μg/m³ 会崩，统一转 UTF-8
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = Path(__file__).parent
FRONTEND_DATA = BASE.parent / "eco-monitor" / "public" / "data"
DEFAULT_JSON = FRONTEND_DATA / "ndvi.json"

T = 50               # 输入时间窗口（期）
HORIZON = 12         # 输出未来期数（文档「12 输出通道」）
FEATURES = ["ndvi", "evi"]   # 有真实长期历史的指标（MODIS 2000 至今）
D_MODEL = 32
N_LAYERS = 2
N_HEADS = 2
FFN = 64
DROPOUT = 0.1
EPOCHS = 300
LR = 1e-3
PATIENCE = 40
SEED = 0

CLIP = {"ndvi": (-1.0, 1.0), "evi": (-1.0, 1.5)}  # 物理合理范围（仅软截断）


def add_months(ym, k):
    y, m = int(ym[:4]), int(ym[5:7])
    total = y * 12 + (m - 1) + k
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def load_history(path):
    """读 modisHistory（长期，优先）否则 timeseries，返回 (months, {feat: [vals]})。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    hist = data.get("modisHistory") or data.get("timeseries") or []
    months, cols = [], {f: [] for f in FEATURES}
    for h in hist:
        vals = {f: h.get(f) for f in FEATURES}
        if all(v is not None and np.isfinite(float(v)) for v in vals.values()):
            months.append(h["month"])
            for f in FEATURES:
                cols[f].append(float(vals[f]))
    return months, cols


def make_windows(X, T, horizon):
    xs, ys = [], []
    for i in range(len(X) - T - horizon + 1):
        xs.append(X[i:i + T])
        ys.append(X[i + T:i + T + horizon])
    return np.asarray(xs, dtype=np.float32), np.asarray(ys, dtype=np.float32)


def build_payload(months, cols, fut, sigma, model_tag, note):
    """fut: [horizon, C] 反归一化后的未来值；sigma: [C] 残差标准差。"""
    N = len(months)
    fut_months = [add_months(months[-1], k + 1) for k in range(HORIZON)]
    series = {}
    for j, f in enumerate(FEATURES):
        lo, hi = CLIP.get(f, (None, None))
        fv = np.clip(fut[:, j], lo, hi) if lo is not None else fut[:, j]
        up = np.clip(fut[:, j] + 1.96 * sigma[j], lo, hi) if lo is not None else fut[:, j] + 1.96 * sigma[j]
        low = np.clip(fut[:, j] - 1.96 * sigma[j], lo, hi) if lo is not None else fut[:, j] - 1.96 * sigma[j]
        series[f] = {
            "labels": months + fut_months,
            "history": [round(float(v), 4) for v in cols[f]] + [None] * HORIZON,
            "future": [None] * N + [round(float(v), 4) for v in fv],
            "upper": [None] * N + [round(float(v), 4) for v in up],
            "lower": [None] * N + [round(float(v), 4) for v in low],
        }
    return {
        "model": model_tag,
        "generatedAt": datetime.now().strftime("%Y-%m-%d"),
        "note": note,
        "horizon": HORIZON,
        "features": FEATURES,
        "inputChannels": T * len(FEATURES),
        "outputChannels": HORIZON,
        "targets": FEATURES,
        "series": series,
    }


def check_only(path):
    months, cols = load_history(path)
    N = len(months)
    C = len(FEATURES)
    print(f"[check] 历史 {N} 期 × {C} 指标（{FEATURES}），范围 {months[0]} ~ {months[-1]}" if N else "[check] 无可用历史点")
    if N < T + HORIZON + 10:
        print(f"[check] 历史点不足（{N} < {T + HORIZON + 10}），会跳过训练")
        return
    X = np.stack([cols[f] for f in FEATURES], axis=1)
    mean, std = X.mean(axis=0), X.std(axis=0) + 1e-6
    Xw, Yw = make_windows((X - mean) / std, T, HORIZON)
    print(f"[check] 输入通道 {T}×{C}={T * C} → 输出 {HORIZON} 期；窗口 {len(Xw)} 个")
    print(f"[check] Xw {Xw.shape}  Yw {Yw.shape}")


def train(path):
    months, cols = load_history(path)
    N = len(months)
    C = len(FEATURES)
    if N < T + HORIZON + 10:
        print(f"历史点不足（{N} < {T + HORIZON + 10}），跳过 Transformer，保留 baseline 预测")
        return False

    X = np.stack([cols[f] for f in FEATURES], axis=1).astype(np.float32)
    mean = X.mean(axis=0)
    std = X.std(axis=0) + 1e-6
    Xn = (X - mean) / std
    Xw, Yw = make_windows(Xn, T, HORIZON)
    n = len(Xw)
    n_val = max(1, int(n * 0.2))
    n_tr = n - n_val
    if n_tr < 10:
        print(f"训练窗口过少（{n}），跳过 Transformer")
        return False

    try:
        import torch
        import torch.nn as nn
    except ImportError:
        print("未安装 torch，跳过 Transformer 训练（保留 baseline 预测）")
        return False

    torch.manual_seed(SEED)
    np.random.seed(SEED)

    Xtr = torch.tensor(Xw[:n_tr])
    Ytr = torch.tensor(Yw[:n_tr])
    Xval = torch.tensor(Xw[n_tr:])
    Yval = torch.tensor(Yw[n_tr:])

    model = EncoderRegressor(C, C, HORIZON, D_MODEL, N_LAYERS, N_HEADS, FFN, DROPOUT)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    lossf = nn.MSELoss()

    best_val = float("inf")
    best_state = None
    patience = PATIENCE
    for ep in range(EPOCHS):
        model.train()
        pred = model(Xtr)
        loss = lossf(pred, Ytr)
        opt.zero_grad()
        loss.backward()
        opt.step()

        model.eval()
        with torch.no_grad():
            vloss = lossf(model(Xval), Yval).item()
        if vloss < best_val:
            best_val = vloss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience = PATIENCE
        else:
            patience -= 1
            if patience <= 0:
                break

    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        last = torch.tensor(Xn[-T:]).unsqueeze(0)
        fut = model(last)[0].numpy()                       # [horizon, C]
        valpred = model(Xval).numpy()                      # [n_val, horizon, C]

    fut = fut * std + mean                                 # 反归一化
    sigma = np.sqrt(np.mean((valpred - Yw[n_tr:]) ** 2, axis=(0, 1)))  # [C] 归一化 RMSE
    sigma = sigma * std                                    # 反归一化

    note = (
        f"输入 {T}×{C}={T * C} 通道 → 输出 {HORIZON} 期；"
        f"文档全量 1048 ≈ 21 指标 × 50 步，当前用真实长期历史 {C} 指标（{'/'.join(FEATURES)}）。"
        f"训练/验证 MSE={loss.item():.4f}/{best_val:.4f}（{ep + 1} epoch）。"
    )
    payload = build_payload(months, cols, fut, sigma, "itransformer-encoder-regressor", note)
    out_path = FRONTEND_DATA / "prediction.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {out_path}")
    print(f"  未来首期 NDVI={fut[0, 0]:.4f}  EVI={fut[0, 1]:.4f}（σ={sigma[0]:.4f}/{sigma[1]:.4f}）")
    return True


def _define_model():
    """torch 仅在实际训练时导入，--check 无需 torch。"""
    import torch
    import torch.nn as nn

    class EncoderRegressor(nn.Module):
        def __init__(self, n_features, n_targets, horizon, d_model=32, n_layers=2, n_heads=2, ffn=64, dropout=0.1):
            super().__init__()
            self.in_proj = nn.Linear(n_features, d_model)
            self.pos = nn.Parameter(torch.randn(1, T, d_model) * 0.02)
            layer = nn.TransformerEncoderLayer(d_model, n_heads, ffn, dropout, batch_first=True, norm_first=True)
            self.encoder = nn.TransformerEncoder(layer, n_layers)
            self.regressor = nn.Sequential(
                nn.Linear(d_model, ffn), nn.ReLU(), nn.Linear(ffn, horizon * n_targets),
            )
            self.horizon = horizon
            self.n_targets = n_targets

        def forward(self, x):                      # x: [B, T, C]
            h = self.in_proj(x) + self.pos[:, :x.size(1), :]
            h = self.encoder(h)                     # [B, T, d_model]
            h = h.mean(dim=1)                       # [B, d_model]
            out = self.regressor(h)                 # [B, horizon*n_targets]
            return out.view(-1, self.horizon, self.n_targets)

    return EncoderRegressor


def main():
    json_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else DEFAULT_JSON
    if "--check" in sys.argv:
        check_only(json_path)
        return
    EncoderRegressor = _define_model()
    globals()["EncoderRegressor"] = EncoderRegressor
    train(json_path)


if __name__ == "__main__":
    main()
