# -*- coding: utf-8 -*-
"""
计算 NDWI = (Green - NIR) / (Green + NIR)，提取水体，输出 result/NDWI.tif（全分辨率）+ result/NDWI.png（网页预览）

用法：python ndwi.py
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


green, profile = read(DATA / "green.tif")
nir, _ = read(DATA / "nir.tif")

green = green / 10000.0
nir = nir / 10000.0

ndwi = np.clip((green - nir) / (green + nir + 1e-6), -1, 1)

profile.update(dtype="float32", count=1, driver="GTiff", nodata=None)
with rasterio.open(RESULT / "NDWI.tif", "w", **profile) as dst:
    dst.write(ndwi, 1)

save_preview(ndwi, RESULT / "NDWI.png", "Blues")

valid = ndwi[np.isfinite(ndwi)]
print(f"NDWI 均值 {valid.mean():.4f}  最小 {valid.min():.4f}  最大 {valid.max():.4f}")
print(f"水体面积(NDWI>0.2 占比) {(valid > 0.2).mean():.2%}")
print("已输出:", RESULT / "NDWI.tif", RESULT / "NDWI.png")
