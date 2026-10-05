# -*- coding: utf-8 -*-
"""
计算地表温度 LST（热度），基于 Landsat 8/9 Collection 2 Level-2 表面温度产品 ST_B10。

Landsat C2 L2 的 ST_B10 波段（Planetary Computer 里资产键为 lwir11）已是经大气校正
与比辐射率订正的地表温度（单位 K），直接换算成摄氏度即可，无需自行订正。

输出 result/LST.tif + result/LST.png。
Landsat 重访 8~16 天，云多时可能无最近可用影像；找不到则跳过（不报错）。
用法：python lst.py
"""
import json
import numpy as np
import rasterio
import planetary_computer
import pystac_client
import matplotlib
matplotlib.use("Agg")
from matplotlib import colormaps
from PIL import Image
from pathlib import Path
from datetime import datetime, timedelta
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds
from rasterio.crs import CRS

BBOX = [104.3, 28.4, 105.1, 29.0]

BASE = Path(__file__).parent
RESULT = BASE / "result"
RESULT.mkdir(exist_ok=True)

# Landsat C2 L2 定标系数（固定值）
ST_SCALE = 0.00341802     # ST_B10 DN -> 开尔文
ST_OFFSET = 149.0

# qa_pixel 里要剔除的位：0 填充 / 1 膨胀云 / 2 卷云 / 3 云 / 4 云影
CLOUD_BITS = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4)

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

_end = datetime.utcnow()
_start = _end - timedelta(days=90)
search = catalog.search(
    collections=["landsat-c2-l2"],
    bbox=BBOX,
    datetime=f"{_start.date().isoformat()}/{_end.date().isoformat()}",
    query={"eo:cloud_cover": {"lt": 60}},
    limit=20,
)
items = [it for it in search.item_collection()
         if "lwir11" in it.assets and "red" in it.assets and "qa_pixel" in it.assets]
print(f"找到 {len(items)} 景 Landsat 影像（云量<60%，含热红外）")

if not items:
    print("未找到可用 Landsat 影像，跳过 LST。")
    raise SystemExit(0)

item = min(items, key=lambda x: x.properties.get("eo:cloud_cover", 100))
print(f"选中: {item.id}  云量 {item.properties.get('eo:cloud_cover')}%  日期 {item.datetime.date()}")


def bbox_window(src):
    left, bottom, right, top = transform_bounds(CRS.from_epsg(4326), src.crs, *BBOX)
    win = from_bounds(left, bottom, right, top, transform=src.transform)
    win = win.intersection(Window(0, 0, src.width, src.height))
    return Window(int(win.col_off), int(win.row_off), int(win.width), int(win.height))


def read_resized(item, key, ref_shape):
    """读某个 30m 波段，裁剪 bbox，再重采样到 ref_shape（与 red 对齐）。"""
    with rasterio.open(item.assets[key].href) as src:
        win = bbox_window(src)
        arr = src.read(1, window=win).astype(np.float32)
    img = Image.fromarray(arr).resize((ref_shape[1], ref_shape[0]), Image.NEAREST)
    return np.asarray(img)


# 用 red 的网格做参考
with rasterio.open(item.assets["red"].href) as src:
    win = bbox_window(src)
    red = src.read(1, window=win).astype(np.float32)
    profile = src.profile.copy()
    profile.update(width=win.width, height=win.height, transform=src.window_transform(win))
ref_shape = red.shape

qa = read_resized(item, "qa_pixel", ref_shape)
st = read_resized(item, "lwir11", ref_shape)

# ST_B10 已订正地表温度（K）-> 摄氏度
lst_c = st * ST_SCALE + ST_OFFSET - 273.15

# 掩膜：云/云影 + 填充像元（DN=0）
bad = (qa.astype(np.int32) & CLOUD_BITS) != 0
bad |= (st == 0)
lst_c = np.where(bad, np.nan, lst_c)
lst_c = np.clip(lst_c, 0, 55)

profile.update(dtype="float32", count=1, driver="GTiff", nodata=None)
with rasterio.open(RESULT / "LST.tif", "w", **profile) as dst:
    dst.write(lst_c, 1)


def save_preview(arr, path, cmap_name, vmin, vmax, max_side=900):
    filled = np.where(np.isfinite(arr), arr, vmin)
    norm = np.clip((filled - vmin) / (vmax - vmin), 0.0, 1.0)
    rgb = colormaps[cmap_name](norm)
    rgb = (rgb[:, :, :3] * 255).astype(np.uint8)
    img = Image.fromarray(rgb, "RGB")
    h, w = arr.shape
    scale = max_side / max(h, w)
    if scale < 1:
        img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    img.save(path, optimize=True)


save_preview(lst_c, RESULT / "LST.png", "RdYlBu_r", 15, 50)

# 记录 LST 影像日期（Landsat，与 Sentinel-2 快照日期不同）
(RESULT / "lst_meta.json").write_text(
    json.dumps({"date": item.datetime.date().isoformat(), "scene_id": item.id}, ensure_ascii=False),
    encoding="utf-8",
)

valid = lst_c[np.isfinite(lst_c)]
print(f"LST 均值 {valid.mean():.2f}°C  最小 {valid.min():.2f}°C  最大 {valid.max():.2f}°C  有效像元 {valid.size}/{lst_c.size}")
print("已输出:", RESULT / "LST.tif", RESULT / "LST.png")
