# -*- coding: utf-8 -*-
"""
净初级生产力 NPP：MODIS MOD17A3HGF 年度净初级生产力（500m，kgC/m²/年）。

数据源：Planetary Computer 集合 `modis-17A3HGF-061`（Terra，Gap-Filled 年产品）。
取最近一年的产品，裁剪宜宾范围，换算成 gC/m²·a（与前端演示单位一致）。

输出 result/npp.json。
用法：python npp.py
"""
import json
import numpy as np
import rasterio
import planetary_computer
import pystac_client
from pathlib import Path
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds
from rasterio.crs import CRS

BBOX = [104.3, 28.4, 105.1, 29.0]
BASE = Path(__file__).parent
RESULT = BASE / "result"
RESULT.mkdir(exist_ok=True)

# Npp_500m 有效值 0~30000（即 0~3.0 kgC/m²/年）；32761~32767 为填充/水体/城市等无值
FILL_MIN = 32761

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)
search = catalog.search(collections=["modis-17A3HGF-061"], bbox=BBOX, limit=10)


def _sort_key(it):
    # 年产品 datetime 可能为 None，退回 start_datetime / id
    if it.datetime is not None:
        return it.datetime.isoformat()
    return it.properties.get("start_datetime") or it.properties.get("datetime") or it.id


items = sorted(search.item_collection(), key=_sort_key, reverse=True)
if not items:
    print("无 MOD17A3HGF 影像")
    raise SystemExit(1)

item = items[0]
if item.datetime is not None:
    year = item.datetime.date().isoformat()
else:
    year = (item.properties.get("start_datetime") or item.id)[:4]
print("选中 NPP 影像:", item.id, "年份", year)

with rasterio.open(item.assets["Npp_500m"].href) as src:
    scale = src.scales[0] if src.scales else 0.0001
    left, bottom, right, top = transform_bounds(CRS.from_epsg(4326), src.crs, *BBOX)
    win = from_bounds(left, bottom, right, top, transform=src.transform)
    win = win.intersection(Window(0, 0, src.width, src.height))
    win = Window(int(win.col_off), int(win.row_off), int(win.width), int(win.height))
    arr = src.read(1, window=win).astype(np.float64)

arr[arr >= FILL_MIN] = np.nan
npp = arr * scale * 1000.0   # kgC/m²/年 -> gC/m²/年
valid = npp[np.isfinite(npp)]

out = {
    "mean": round(float(valid.mean()), 1),
    "median": round(float(np.median(valid)), 1),
    "min": round(float(valid.min()), 1),
    "max": round(float(valid.max()), 1),
    "unit": "gC/m²·a",
    "pixels": int(valid.size),
    "date": year,
    "scene_id": item.id,
}

path = RESULT / "npp.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("已输出:", path)
print(json.dumps(out, ensure_ascii=False, indent=2))
