# -*- coding: utf-8 -*-
"""
计算扩展生态指数（基于 Sentinel-2 L2A 地表反射率）：
    EVI    增强植被指数
    NDBSI  干度（RSEI 分量：IBI 建筑指数 + SI 土壤指数 的均值）
    WET    湿度（缨帽变换湿度分量，Sentinel-2 系数）

输出 result/EVI.tif、NDBSI.tif、WET.tif（10m 全分辨率）+ 网页预览 PNG。

依赖 download.py 下载的波段：blue(B02) green(B03) red(B04) nir(B08) swir(B11) swir2(B12)
用法：python indices.py
"""
import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
from matplotlib import colormaps
from PIL import Image
from pathlib import Path
from rasterio.enums import Resampling

BASE = Path(__file__).parent
DATA = BASE / "data"
RESULT = BASE / "result"
RESULT.mkdir(exist_ok=True)


def read(path):
    with rasterio.open(path) as src:
        return src.read(1).astype(np.float32), src.profile


def read_20m(path, ref_shape):
    """读 20m 波段并用双线性重采样到 10m 参考网格（ref_shape = 10m 波段形状）。"""
    with rasterio.open(path) as src:
        return src.read(1, out_shape=ref_shape, resampling=Resampling.bilinear).astype(np.float32)


def save_preview(arr, path, cmap_name, vmin=-1.0, vmax=1.0, max_side=900):
    """把指数数组上色后缩成网页预览 PNG。"""
    norm = np.clip((arr - vmin) / (vmax - vmin), 0.0, 1.0)
    rgb = colormaps[cmap_name](norm)
    rgb = (rgb[:, :, :3] * 255).astype(np.uint8)
    img = Image.fromarray(rgb, "RGB")
    h, w = arr.shape
    scale = max_side / max(h, w)
    if scale < 1:
        img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    img.save(path, optimize=True)


blue, _ = read(DATA / "blue.tif")
green, _ = read(DATA / "green.tif")
red, profile = read(DATA / "red.tif")
nir, _ = read(DATA / "nir.tif")

# 20m 波段重采样到 10m 网格（与 red 同形状）
swir = read_20m(DATA / "swir.tif", red.shape)
swir2 = read_20m(DATA / "swir2.tif", red.shape)

# L2A 反射率按 ×10000 存储，还原到 0~1
blue /= 10000.0
green /= 10000.0
red /= 10000.0
nir /= 10000.0
swir /= 10000.0
swir2 /= 10000.0

# EVI = 2.5*(NIR-RED)/(NIR+6*RED-7.5*BLUE+1)
evi = np.clip(2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1 + 1e-6), -1, 1)

# SI 土壤指数 + IBI 建筑指数 -> 干度 NDBSI = (IBI+SI)/2
si = ((swir + red) - (nir + blue)) / ((swir + red) + (nir + blue) + 1e-6)
a = 2 * swir / (swir + nir + 1e-6)
b = nir / (nir + red + 1e-6) + green / (green + swir + 1e-6)
ibi = (a - b) / (a + b + 1e-6)
ndbsi = np.clip((ibi + si) / 2, -1, 1)

# WET 湿度（缨帽变换湿度分量，Sentinel-2 系数）
wet = np.clip(0.1511 * blue + 0.1973 * green + 0.3283 * red + 0.3407 * nir
              - 0.7117 * swir - 0.4559 * swir2, -1, 1)

# NDVI（供 FVC 使用）
ndvi = (nir - red) / (nir + red + 1e-6)

# FVC 植被覆盖度（像元二分模型，NDVI_soil=0.05，NDVI_veg=0.7）
fvc = np.clip((ndvi - 0.05) / (0.7 - 0.05), 0, 1)

# LAI 叶面积指数（经验模型 Boegh 2002：LAI = 3.618*EVI - 0.118）
lai = np.clip(3.618 * evi - 0.118, 0, 8)


def write(arr, name, cmap, vmin, vmax):
    profile.update(dtype="float32", count=1, driver="GTiff", nodata=None)
    with rasterio.open(RESULT / f"{name}.tif", "w", **profile) as dst:
        dst.write(arr, 1)
    save_preview(arr, RESULT / f"{name}.png", cmap, vmin, vmax)
    valid = arr[np.isfinite(arr)]
    print(f"{name} 均值 {valid.mean():.4f}  最小 {valid.min():.4f}  最大 {valid.max():.4f}")


write(evi, "EVI", "YlGn", -0.2, 0.8)
write(ndbsi, "NDBSI", "YlOrBr", -0.4, 0.6)
write(wet, "WET", "YlGnBu", -0.6, 0.1)
write(fvc, "FVC", "YlGn", 0.0, 1.0)
write(lai, "LAI", "Greens", 0.0, 5.0)
print("已输出:", RESULT / "EVI.tif", RESULT / "NDBSI.tif", RESULT / "WET.tif",
      RESULT / "FVC.tif", RESULT / "LAI.tif")
