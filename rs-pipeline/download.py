# -*- coding: utf-8 -*-
"""
下载 / 读取宜宾区域 Sentinel-2 L2A 波段（只切 bbox，不下载整景几十 GB）

依赖：pystac-client  planetary-computer  rasterio
用法：
    conda activate remote
    python download.py
"""
import planetary_computer
import pystac_client
import rasterio
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds
from rasterio.crs import CRS
from pathlib import Path
from datetime import datetime, timedelta

# 宜宾主城区及三江（长江/金沙江/岷江）交汇范围 [min_lon, min_lat, max_lon, max_lat]
BBOX = [104.3, 28.4, 105.1, 29.0]

# 需要的波段：红 / 绿 / 近红外 / 短波红外
BANDS = {"red": "B04", "green": "B03", "blue": "B02", "nir": "B08", "swir": "B11", "swir2": "B12"}

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

# 时间窗：最近 180 天（实时更新：每次运行自动纳入最新影像）
_end = datetime.utcnow()
_start = _end - timedelta(days=180)

search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=BBOX,
    datetime=f"{_start.date().isoformat()}/{_end.date().isoformat()}",
    query={"eo:cloud_cover": {"lt": 10}},  # 云量 < 10%
    limit=10,
)
items = list(search.item_collection())
print(f"找到 {len(items)} 景影像")

if not items:
    raise SystemExit("没有找到符合条件的影像，请放宽时间或云量限制后重试")

item = min(items, key=lambda x: x.properties.get("eo:cloud_cover", 100))
date = item.datetime.date().isoformat()
print("选中:", item.id)
print("云量:", item.properties.get("eo:cloud_cover"), "%")
print("日期:", date)

# 记录本次选中的影像日期，供 export_frontend.py 使用
(OUT / "meta.json").write_text(
    '{"date": "%s", "scene_id": "%s"}' % (date, item.id), encoding="utf-8"
)

for name, band in BANDS.items():
    with rasterio.open(item.assets[band].href) as src:
        # 1) 经纬度 bbox（EPSG:4326）转成影像自身坐标系（通常为 UTM）
        left, bottom, right, top = transform_bounds(
            CRS.from_epsg(4326), src.crs, *BBOX
        )
        win = from_bounds(left, bottom, right, top, transform=src.transform)

        # 2) 裁剪到影像有效范围（bbox 可能超出这一景）
        win = win.intersection(Window(0, 0, src.width, src.height))
        if win.width <= 0 or win.height <= 0:
            print(f"{name}: bbox 与该景无交集，跳过")
            continue

        # 3) 窗口取整
        win = Window(int(win.col_off), int(win.row_off), int(win.width), int(win.height))
        arr = src.read(1, window=win)
        profile = src.profile.copy()
        profile.update(
            width=win.width,
            height=win.height,
            transform=src.window_transform(win),
        )
        dst_path = OUT / f"{name}.tif"
        with rasterio.open(dst_path, "w", **profile) as dst:
            dst.write(arr, 1)
        print(f"{name} -> {arr.shape} {arr.dtype} -> {dst_path}")

print("完成。下一步：python ndvi.py && python ndwi.py")
