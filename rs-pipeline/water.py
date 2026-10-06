# -*- coding: utf-8 -*-
"""
水体反演：浮游藻类指数 FAI + 浑浊度 Turbidity（基于 Sentinel-2 L2A 地表反射率）。

四川盆地气溶胶/霾较强，L2A 在水体上残留大气程辐射（本场景 SWIR 本底 ~0.1，清水应 ~0.01）。
处理方式：
- FAI（漂浮藻类指数，Hu 2009，SWIR 基线插值）是「光谱形状」指数，加性程辐射在基线
  相减中相互抵消，对霾稳健：
      FAI = R(B8) - [R(B4) + (λB8-λB4)/(λB11-λB4) × (R(B11) - R(B4))]
  正值表示存在漂浮藻类。
- 浑浊度（Dogliotti 2015 红波段算法）需要绝对离水反射率，先做「SWIR 暗像元扣除」：
  水体在 SWIR 近似黑，故 ρ_water(red) ≈ ρ(red) - ρ(SWIR)，再
      T = 228.1 × ρ / (1 - ρ / 0.1641)，单位 NTU/FNU。

水体掩膜：NDWI = (Green-NIR)/(Green+NIR) > 0.1（长江水体浑浊、NIR 抬高，阈值取 0.1）。

输出 result/water.json（mean/median/p10/p90 均在水体像元内统计）。
用法：python water.py
"""
import json
import numpy as np
import rasterio
from pathlib import Path
from rasterio.enums import Resampling

BASE = Path(__file__).parent
DATA = BASE / "data"
RESULT = BASE / "result"
RESULT.mkdir(exist_ok=True)

# Sentinel-2 波段中心波长
WL_RED, WL_NIR, WL_SWIR = 664.6, 832.8, 1613.7


def read(path):
    with rasterio.open(path) as src:
        return src.read(1).astype(np.float32)


def read_20m(path, ref_shape):
    """20m 波段重采样到 10m 网格。"""
    with rasterio.open(path) as src:
        return src.read(1, out_shape=ref_shape, resampling=Resampling.bilinear).astype(np.float32)


red = read(DATA / "red.tif") / 10000.0        # B04
green = read(DATA / "green.tif") / 10000.0    # B03
nir = read(DATA / "nir.tif") / 10000.0        # B08
swir = read_20m(DATA / "swir.tif", red.shape) / 10000.0  # B11

# 水体掩膜：NDWI > 0.1
ndwi = (green - nir) / (green + nir + 1e-6)
water = (ndwi > 0.1) & np.isfinite(red) & np.isfinite(nir) & np.isfinite(swir)
print(f"水体像元占比 {water.mean():.2%}")

# FAI（SWIR 基线插值，霾稳健）
w = (WL_NIR - WL_RED) / (WL_SWIR - WL_RED)
fai = nir - (red + w * (swir - red))

# 浑浊度（SWIR 暗像元扣除大气程辐射 + Dogliotti 2015 红波段）
rho_w = np.clip(red - swir, 0.0, 0.15)
turb = 228.1 * rho_w / (1.0 - rho_w / 0.1641)


def stats(arr, mask):
    v = arr[mask & np.isfinite(arr)]
    return {
        "mean": round(float(v.mean()), 4),
        "median": round(float(np.median(v)), 4),
        "p10": round(float(np.percentile(v, 10)), 4),
        "p90": round(float(np.percentile(v, 90)), 4),
        "pixels": int(v.size),
    }


out = {
    "fai": {**stats(fai, water), "unit": "", "note": "正值表示漂浮藻类"},
    "turbidity": {**stats(turb, water), "unit": "NTU"},
}

meta = DATA / "meta.json"
if meta.exists():
    out["date"] = json.loads(meta.read_text(encoding="utf-8")).get("date")

path = RESULT / "water.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("已输出:", path)
print(json.dumps(out, ensure_ascii=False, indent=2))
