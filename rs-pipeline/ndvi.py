# -*- coding: utf-8 -*-
"""
计算 NDVI = (NIR - Red) / (NIR + Red)，输出 result/NDVI.tif（全分辨率）+ result/NDVI.png（网页预览）

用法：python ndvi.py
"""
import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
from matplotlib import colormaps
from PIL import Image
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
RESULT = BASE / "result"
RESULT.mkdir(exist_ok=True)


def read(path):
    with rasterio.open(path) as src:
        return src.read(1).astype(np.float32), src.profile


def save_preview(arr, path, cmap_name, max_side=900):
    """把 [-1, 1] 的指数数组上色后，缩小成长边 max_side 的 PNG（用于网页预览，避免 4000px 大图）。"""
    norm = np.clip(arr, -1.0, 1.0) / 2.0 + 0.5          # -> 0..1
    rgb = colormaps[cmap_name](norm)                    # (h, w, 4) float 0..1
    rgb = (rgb[:, :, :3] * 255).astype(np.uint8)
    img = Image.fromarray(rgb, "RGB")
    h, w = arr.shape
    scale = max_side / max(h, w)
    if scale < 1:
        img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    img.save(path, optimize=True)


red, profile = read(DATA / "red.tif")
nir, _ = read(DATA / "nir.tif")

# Sentinel-2 L2A 地表反射率按 ×10000 存储，先还原到 0~1（关键一步！）
red = red / 10000.0
nir = nir / 10000.0

ndvi = np.clip((nir - red) / (nir + red + 1e-6), -1, 1)

profile.update(dtype="float32", count=1, driver="GTiff", nodata=None)
with rasterio.open(RESULT / "NDVI.tif", "w", **profile) as dst:
    dst.write(ndvi, 1)

save_preview(ndvi, RESULT / "NDVI.png", "RdYlGn")

valid = ndvi[np.isfinite(ndvi)]
print(f"NDVI 均值 {valid.mean():.4f}  最小 {valid.min():.4f}  最大 {valid.max():.4f}")
print(f"植被覆盖(NDVI>0.3 占比) {(valid > 0.3).mean():.2%}")
print("已输出:", RESULT / "NDVI.tif", RESULT / "NDVI.png")
