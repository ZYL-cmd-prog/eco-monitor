# -*- coding: utf-8 -*-
"""
生成演示用 NDVI/NDWI 图片（合成数据，仅供前端预览）。
跑通 download.py + ndvi.py + ndwi.py + export_frontend.py 后，会被真实数据替换。

用法：python make_demo.py
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).parent.parent / "eco-monitor" / "public" / "data"
OUT.mkdir(parents=True, exist_ok=True)

H, W = 480, 640
y, x = np.mgrid[0:H, 0:W]

# 模拟一条自北向南蜿蜒的河流（长江 / 金沙江）
river_x = W * 0.5 + 60 * np.sin(y / H * 2 * np.pi) + 30 * np.sin(y / H * 5 * np.pi)
water = (np.abs(x - river_x) < 14).astype(np.float32)

rng = np.random.default_rng(7)

# NDVI：陆地植被高、水体/城区低
base = 0.55 + 0.15 * (1 - x / W) + 0.10 * (1 - y / H)
noise = rng.normal(0, 0.05, (H, W)).astype(np.float32)
ndvi = np.clip(base - 0.8 * water + noise, -1, 1)

# NDWI：水体高、陆地低（与 NDVI 大致相反）
ndwi = np.clip(-0.35 + 0.9 * water + rng.normal(0, 0.04, (H, W)).astype(np.float32), -1, 1)

plt.imsave(OUT / "NDVI.png", ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
plt.imsave(OUT / "NDWI.png", ndwi, cmap="Blues", vmin=-1, vmax=1)
print("已生成演示图 ->", OUT)
