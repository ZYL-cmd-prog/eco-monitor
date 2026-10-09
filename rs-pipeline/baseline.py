# -*- coding: utf-8 -*-
"""
baseline.py — 预测基线：趋势 + 季节性（月气候态）

作用
----
读前端 public/data/ndvi.json 里的长期时序（优先 modisHistory，MODIS 2000 年至今；
否则回退 timeseries 的近期 Sentinel-2），用「线性趋势 + 各月平均季节项」预测未来
12 个月，用「历史残差标准差」给出 95% 置信区间，输出前端「智能分析」页
Analysis.vue 需要的 prediction.json 形状：

    { labels, history, future, upper, lower }（四序列补成完整长度，缺失段填 None）

数据点不足 2 年时退回线性趋势外推。

用法
----
    python baseline.py [ndvi.json 路径] [指标名，默认 ndvi]
输出
----
    prediction.json（写到前端 public/data/）
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

BASE = Path(__file__).parent
FRONTEND_DATA = BASE.parent / "eco-monitor" / "public" / "data"
DEFAULT_JSON = FRONTEND_DATA / "ndvi.json"


def add_months(ym: str, k: int) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    total = y * 12 + (m - 1) + k
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def load_timeseries(path: Path, key: str):
    data = json.loads(path.read_text(encoding="utf-8"))
    # 优先长期 MODIS 历史（2000 年至今），否则回退近期 Sentinel-2 时序
    ts = data.get("modisHistory") or data.get("timeseries") or []
    months, vals = [], []
    for t in ts:
        v = t.get(key)
        if v is None:
            continue
        months.append(t["month"])
        vals.append(float(v))
    return months, vals


def linear_forecast(vals, horizon=12):
    x = np.arange(len(vals), dtype=float)
    y = np.asarray(vals, dtype=float)
    b, a = np.polyfit(x, y, 1)
    trend = a + b * x
    sigma = float((y - trend).std(ddof=1)) if len(y) > 2 else 0.0
    xf = np.arange(len(vals), len(vals) + horizon, dtype=float)
    future = [round(float(v), 4) for v in (a + b * xf)]
    upper = [round(float(v), 4) for v in (a + b * xf + 1.96 * sigma)]
    lower = [round(float(v), 4) for v in (a + b * xf - 1.96 * sigma)]
    return future, upper, lower


def seasonal_forecast(months, vals, horizon=12):
    """趋势 + 月气候态：y = 线性趋势 + 各月平均季节项。"""
    y = np.asarray(vals, dtype=float)
    x = np.arange(len(y), dtype=float)
    b, a = np.polyfit(x, y, 1)
    trend = a + b * x
    mi = np.array([int(m[5:7]) for m in months])     # 1..12
    seasonal = np.zeros(12)
    resid = y - trend
    for m in range(1, 13):
        mask = mi == m
        if mask.any():
            seasonal[m - 1] = resid[mask].mean()
    fitted = trend + seasonal[mi - 1]
    sigma = float((y - fitted).std(ddof=1)) if len(y) > 12 else float(resid.std(ddof=1))

    fut_months = [add_months(months[-1], i + 1) for i in range(horizon)]
    fut_mi = np.array([int(m[5:7]) for m in fut_months])
    xf = np.arange(len(y), len(y) + horizon, dtype=float)
    fut = (a + b * xf) + seasonal[fut_mi - 1]
    return (fut_months,
            [round(float(v), 4) for v in fut],
            [round(float(v), 4) for v in (fut + 1.96 * sigma)],
            [round(float(v), 4) for v in (fut - 1.96 * sigma)])


def main():
    json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JSON
    key = sys.argv[2] if len(sys.argv) > 2 else "ndvi"

    months, vals = load_timeseries(json_path, key)
    if len(vals) < 3:
        print(f"时序点太少（{len(vals)}），无法拟合趋势，跳过")
        return

    horizon = 12
    if len(vals) >= 24:
        fut_months, future, upper, lower = seasonal_forecast(months, vals, horizon)
        model = "baseline-seasonal-trend"
    else:
        future, upper, lower = linear_forecast(vals, horizon)
        fut_months = [add_months(months[-1], i + 1) for i in range(horizon)]
        model = "baseline-linear-trend"

    n = len(vals)
    out = {
        "target": key,
        "model": model,
        "generatedAt": datetime.now().strftime("%Y-%m-%d"),
        "labels": months + fut_months,
        "history": vals + [None] * horizon,
        "future": [None] * n + future,
        "upper": [None] * n + upper,
        "lower": [None] * n + lower,
    }

    out_path = FRONTEND_DATA / "prediction.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已生成 {out_path}")
    print(f"指标={key} 历史 {n} 个月点 -> 预测未来 {horizon} 个月（模型={model}）")
    print(f"历史范围 {months[0]} ~ {months[-1]}，未来末月 {fut_months[-1]}")
    print(f"未来首月 {fut_months[0]}: {future[0]:.4f}  [{lower[0]:.4f}, {upper[0]:.4f}]")
    print(f"未来末月 {fut_months[-1]}: {future[-1]:.4f}  [{lower[-1]:.4f}, {upper[-1]:.4f}]")


if __name__ == "__main__":
    main()
