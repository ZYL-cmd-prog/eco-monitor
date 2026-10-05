# -*- coding: utf-8 -*-
"""
Phase 2：多时相 NDVI/NDWI 时间序列（带 SCL 云掩膜）
拉取生长季（4~10 月）多景 Sentinel-2 L2A，按月挑云量最低的一景，
用 SCL 波段剔除云/云影/卷云像素后，逐景算 bbox 内 NDVI / NDWI 均值，
输出 result/timeseries.json

用法：python timeseries.py
"""
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import rasterio
import planetary_computer
import pystac_client
from PIL import Image
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds
from rasterio.crs import CRS

BBOX = [104.3, 28.4, 105.1, 29.0]
BANDS = {"red": "B04", "green": "B03", "nir": "B08"}
MAX_SIDE = 800          # 降采样到长边 800px，足够算均值，避免下载几十 MB/景
# SCL 里要剔除的像素：0 无数据 / 1 饱和 / 2 暗像元 / 3 云影 / 8 中概率云 / 9 高概率云 / 10 卷云
CLOUD_SCL = {0, 1, 2, 3, 8, 9, 10}

BASE = Path(__file__).parent
RESULT = BASE / "result"
RESULT.mkdir(exist_ok=True)

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

# 时间窗：最近 365 天（实时更新：滚动全年，自动纳入最新月份）
_end = datetime.utcnow()
_start = _end - timedelta(days=365)

search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=BBOX,
    datetime=f"{_start.date().isoformat()}/{_end.date().isoformat()}",
    query={"eo:cloud_cover": {"lt": 60}},
    limit=100,
)
items = list(search.item_collection())
print(f"找到 {len(items)} 景影像（云量<60%）")

# 按月分组，每月取云量最低的一景
by_month = defaultdict(list)
for it in items:
    d = it.datetime.date()
    by_month[(d.year, d.month)].append(it)

selected = []
for month in sorted(by_month):
    best = min(by_month[month], key=lambda x: x.properties.get("eo:cloud_cover", 100))
    selected.append(best)
    print(f"  {month[0]}-{month[1]:02d}: {best.id[:34]}  云量 {best.properties.get('eo:cloud_cover'):.2f}%")


def bbox_window(src):
    """返回 bbox 在 src 自身坐标系里、并裁剪到影像有效范围的窗口。"""
    left, bottom, right, top = transform_bounds(CRS.from_epsg(4326), src.crs, *BBOX)
    win = from_bounds(left, bottom, right, top, transform=src.transform)
    win = win.intersection(Window(0, 0, src.width, src.height))
    return Window(int(win.col_off), int(win.row_off), int(win.width), int(win.height))


def out_shape_for(win):
    h, w = win.height, win.width
    scale = MAX_SIDE / max(h, w)
    if scale >= 1:
        return (int(h), int(w))
    return (max(1, int(h * scale)), max(1, int(w * scale)))


def read_decimated(item, band, win, out_shape):
    with rasterio.open(item.assets[band].href) as src:
        return src.read(1, window=win, out_shape=out_shape).astype(np.float32) / 10000.0


def read_scl_mask(item, out_shape):
    """读 SCL（20m）并按同样地理范围缩放到 out_shape，返回云掩膜 bool 数组。"""
    with rasterio.open(item.assets["SCL"].href) as src:
        win = bbox_window(src)
        scl = src.read(1, window=win)
    img = Image.fromarray(scl).resize((out_shape[1], out_shape[0]), Image.NEAREST)
    scl_resized = np.asarray(img)
    return ~np.isin(scl_resized, list(CLOUD_SCL))


series = []
for it in selected:
    d = it.datetime.date()
    month = f"{d.year}-{d.month:02d}"

    # 用 nir（B08，10m）的 transform 算窗口；B03/B04/B08 同为 10m 且对齐，共用该窗口
    with rasterio.open(it.assets[BANDS["nir"]].href) as src:
        win = bbox_window(src)
        if win.width <= 0 or win.height <= 0:
            print(f"{month}: bbox 无交集，跳过")
            continue
        out_shape = out_shape_for(win)
        nir = read_decimated(it, BANDS["nir"], win, out_shape)
    red = read_decimated(it, BANDS["red"], win, out_shape)
    green = read_decimated(it, BANDS["green"], win, out_shape)

    mask = read_scl_mask(it, out_shape)          # True = 有效（非云）像素
    ndvi = np.clip((nir - red) / (nir + red + 1e-6), -1, 1)
    ndwi = np.clip((green - nir) / (green + nir + 1e-6), -1, 1)
    ndvi = np.where(mask, ndvi, np.nan)
    ndwi = np.where(mask, ndwi, np.nan)

    series.append({
        "month": month,
        "ndvi": round(float(np.nanmean(ndvi)), 4),
        "ndwi": round(float(np.nanmean(ndwi)), 4),
        "cloud": round(float(it.properties.get("eo:cloud_cover", 0)), 2),
        "validPct": round(float(mask.mean()), 4),
    })
    print(f"  {month}: NDVI={series[-1]['ndvi']:.4f}  NDWI={series[-1]['ndwi']:.4f}  "
          f"有效像元 {series[-1]['validPct']*100:.0f}%")

series.sort(key=lambda x: x["month"])
(RESULT / "timeseries.json").write_text(
    json.dumps(series, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"\n已输出 {len(series)} 个时相点 -> {RESULT / 'timeseries.json'}")
