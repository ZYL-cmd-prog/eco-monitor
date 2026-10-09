# -*- coding: utf-8 -*-
"""
baseline.py — 预测基线（Baseline 1：线性趋势外推 + 残差标准差置信区间）

作用
----
读前端 public/data/ndvi.json 里的月度 timeseries（目前仅 ndvi / ndwi 有时序），
用「线性趋势」预测未来 12 个月，用「历史残差标准差」给出置信区间，
输出前端「智能分析」页 Analysis.vue 需要的 prediction.json 形状：

    { labels, history, future, upper, lower }
    （四个序列都是完整长度 = 历史段 + 未来段，缺失段填 None，方便 ECharts 按类别对齐）

这是整套预测的第一步：先用最简单的模型把「数据 -> 预测 -> 前端曲线」闭环跑通。
之后再逐步升级到 滞后特征 + LightGBM（Baseline 2），最后才是 iTransformer。

诚实说明：目前 timeseries 只有 12 个月点，任何模型都只是「演示跑通」，不具备统计意义。
真正要做的下一步是把 MODIS / Landsat 历史存档拉回来，把时序补到 6-20 年。

用法
----
    python baseline.py [ndvi.json 路径] [指标名，默认 ndvi]

输出
----
    prediction.json（写到 ndvi.json 同目录）
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
    """'2025-10' 加 k 个月 -> '2026-10'"""
    y, m = int(ym[:4]), int(ym[5:7])
    total = y * 12 + (m - 1) + k
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def load_timeseries(path: Path, key: str):
    data = json.loads(path.read_text(encoding="utf-8"))
    ts = data.get("timeseries", [])
    months, vals = [], []
    for t in ts:
        v = t.get(key)
        if v is None:
            continue
        months.append(t["month"])
        vals.append(float(v))
    return months, vals


def linear_forecast(vals, horizon=12):
    """线性趋势外推，返回 (future, upper, lower, 截距, 斜率)"""
    x = np.arange(len(vals), dtype=float)
    y = np.asarray(vals, dtype=float)
    b, a = np.polyfit(x, y, 1)          # y = b*x + a
    trend = a + b * x
    sigma = float((y - trend).std(ddof=1)) if len(y) > 2 else 0.0

    xf = np.arange(len(vals), len(vals) + horizon, dtype=float)
    future = [round(v, 4) for v in (a + b * xf)]
    upper = [round(v, 4) for v in (a + b * xf + 1.96 * sigma)]
    lower = [round(v, 4) for v in (a + b * xf - 1.96 * sigma)]
    return future, upper, lower, float(a), float(b)


def main():
    json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JSON
    key = sys.argv[2] if len(sys.argv) > 2 else "ndvi"

    months, vals = load_timeseries(json_path, key)
    if len(vals) < 3:
        print(f"时序点太少（{len(vals)}），无法拟合趋势，跳过")
        return

    horizon = 12
    future, upper, lower, a, b = linear_forecast(vals, horizon)
    fut_months = [add_months(months[-1], i + 1) for i in range(horizon)]
    n = len(vals)

    out = {
        "target": key,
        "model": "baseline-linear-trend",
        "generatedAt": datetime.now().strftime("%Y-%m-%d"),
        "labels": months + fut_months,
        # 四个序列都补到完整长度，未来段/历史段缺失处填 None，便于 ECharts 对齐
        "history": vals + [None] * horizon,
        "future": [None] * n + future,
        "upper": [None] * n + upper,
        "lower": [None] * n + lower,
    }

    out_path = FRONTEND_DATA / "prediction.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已生成 {out_path}")
    print(f"指标={key} 历史 {n} 个月点 -> 预测未来 {horizon} 个月")
    print(f"趋势：y = {a:.4f} + {b:.4f} * x")
    print(f"未来首月 {fut_months[0]}: {future[0]:.4f}  [{lower[0]:.4f}, {upper[0]:.4f}]")
    print(f"未来末月 {fut_months[-1]}: {future[-1]:.4f}  [{lower[-1]:.4f}, {upper[-1]:.4f}]")


if __name__ == "__main__":
    main()
