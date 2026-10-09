# -*- coding: utf-8 -*-
"""
MODIS MOD13Q1 长期 NDVI/EVI 时间序列（2000 年至今，约 26 年）

用于补齐历史时序，支撑趋势预测（baseline.py 的长期基线）。
数据源：Planetary Computer 集合 `modis-13Q1-061`（250m，16 天合成，NDVI+EVI）。
逐景读 bbox 内 NDVI/EVI，用 pixel_reliability 掩膜剔除云/雪/填充像元，
按月聚合为月度均值，输出 result/modis_history.json。

用法：python modis_history.py
"""
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import rasterio
import planetary_computer
import pystac_client
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds
from rasterio.crs import CRS

BBOX = [104.3, 28.4, 105.1, 29.0]
SCALE = 0.0001
VALID_MIN = -0.2              # NDVI/EVI 有效下限（填充值为 -0.3）

BASE = Path(__file__).parent
RESULT = BASE / "result"
RESULT.mkdir(exist_ok=True)

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

_end = datetime.utcnow().date().isoformat()
search = catalog.search(
    collections=["modis-13Q1-061"],
    bbox=BBOX,
    datetime=f"2000-02-18/{_end}",
)
items = list(search.item_collection())
print(f"找到 {len(items)} 景 MOD13Q1")


def item_date(it):
    """MODIS item 的 datetime 常为 None，退回 start_datetime / id 里的 A{年}{日序}。"""
    if it.datetime is not None:
        return it.datetime.date()
    s = it.properties.get("start_datetime")
    if s:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    m = re.search(r"\.A(\d{4})(\d{3})\.", it.id)
    if m:
        year, doy = int(m.group(1)), int(m.group(2))
        return datetime(year, 1, 1).date() + timedelta(days=doy - 1)
    return None


def bbox_window(src):
    left, bottom, right, top = transform_bounds(CRS.from_epsg(4326), src.crs, *BBOX)
    win = from_bounds(left, bottom, right, top, transform=src.transform)
    win = win.intersection(Window(0, 0, src.width, src.height))
    return Window(int(win.col_off), int(win.row_off), int(win.width), int(win.height))


def read_win(item, asset, win):
    with rasterio.open(item.assets[asset].href) as src:
        return src.read(1, window=win).astype(np.float32)


monthly = defaultdict(lambda: {"ndvi": [], "evi": [], "valid": []})
skipped = 0

for i, it in enumerate(items):
    d = item_date(it)
    if d is None:
        skipped += 1
        continue
    try:
        # NDVI/EVI/reliability 同属 250m 网格，共用同一个窗口
        with rasterio.open(it.assets["250m_16_days_NDVI"].href) as src:
            win = bbox_window(src)
            if win.width <= 0 or win.height <= 0:
                skipped += 1
                continue
            ndvi = src.read(1, window=win).astype(np.float32) * SCALE
        evi = read_win(it, "250m_16_days_EVI", win) * SCALE
        rel = read_win(it, "250m_16_days_pixel_reliability", win)
    except Exception:
        skipped += 1
        continue

    # reliability：0 好 / 1 边缘可用；剔除 2 雪 / 3 云 / -1 填充
    good = ((rel == 0) | (rel == 1)) & (ndvi > VALID_MIN) & (evi > VALID_MIN)
    ndvi = np.where(good, ndvi, np.nan)
    evi = np.where(good, evi, np.nan)
    if not np.isfinite(ndvi).any():
        skipped += 1
        continue

    key = f"{d.year}-{d.month:02d}"
    monthly[key]["ndvi"].append(float(np.nanmean(ndvi)))
    monthly[key]["evi"].append(float(np.nanmean(evi)))
    monthly[key]["valid"].append(float(np.isfinite(ndvi).mean()))

    if (i + 1) % 100 == 0:
        print(f"  已处理 {i + 1}/{len(items)}")

series = []
for key in sorted(monthly):
    g = monthly[key]
    series.append({
        "month": key,
        "ndvi": round(float(np.mean(g["ndvi"])), 4),
        "evi": round(float(np.mean(g["evi"])), 4),
        "nScenes": len(g["ndvi"]),
        "validPct": round(float(np.mean(g["valid"])), 4),
    })

series.sort(key=lambda x: x["month"])
(RESULT / "modis_history.json").write_text(
    json.dumps(series, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"\n已输出 {len(series)} 个月 -> {RESULT / 'modis_history.json'}（跳过 {skipped} 景）")
