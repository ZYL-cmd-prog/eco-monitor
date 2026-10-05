# -*- coding: utf-8 -*-
"""
把计算结果导出成前端要的 ndvi.json + 图片，直接写入前端 public/data/

用法：python export_frontend.py
前置：先跑 download.py -> ndvi.py -> ndwi.py
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
import numpy as np
import rasterio

BASE = Path(__file__).parent
RESULT = BASE / "result"
DATA = BASE / "data"
FRONTEND_DATA = BASE.parent / "eco-monitor" / "public" / "data"
FRONTEND_DATA.mkdir(parents=True, exist_ok=True)


def load(path):
    with rasterio.open(path) as src:
        return src.read(1).astype(np.float32)


def stats(a):
    a = a[np.isfinite(a)]
    return {
        "mean": round(float(a.mean()), 4),
        "min": round(float(a.min()), 4),
        "max": round(float(a.max()), 4),
        "std": round(float(a.std()), 4),
    }


ndvi = load(RESULT / "NDVI.tif")
ndwi = load(RESULT / "NDWI.tif")

# 扩展生态指数（EVI/干度/湿度），由 indices.py 生成；文件不存在则跳过
indices = {}
for _key in ("EVI", "NDBSI", "WET", "FVC", "LAI", "LST"):
    _p = RESULT / f"{_key}.tif"
    if _p.exists():
        _a = load(_p)
        indices[_key.lower()] = {**stats(_a), "image": f"/data/{_key}.png"}

# LST 影像日期（Landsat，与 Sentinel-2 快照日期不同）
_lst_meta = RESULT / "lst_meta.json"
if _lst_meta.exists() and "lst" in indices:
    _m = json.loads(_lst_meta.read_text(encoding="utf-8"))
    indices["lst"]["date"] = _m.get("date")
    indices["lst"]["scene_id"] = _m.get("scene_id")

# 大气柱浓度（Sentinel-5P，由 s5p.py 生成；没有则跳过）
atmosphere = None
_s5p = RESULT / "s5p.json"
if _s5p.exists():
    atmosphere = json.loads(_s5p.read_text(encoding="utf-8"))

# 读取 download.py 记录的影像日期
date = "待定"
meta = DATA / "meta.json"
if meta.exists():
    date = json.loads(meta.read_text(encoding="utf-8")).get("date", "待定")

# 读取多时相时间序列（Phase 2，由 timeseries.py 生成；没有则空列表）
timeseries = []
ts_path = RESULT / "timeseries.json"
if ts_path.exists():
    timeseries = json.loads(ts_path.read_text(encoding="utf-8"))

data = {
    "region": "宜宾市 · 长江上游示范区",
    "satellite": "Sentinel-2 L2A",
    "source": "Microsoft Planetary Computer",
    "date": date,
    "generatedAt": datetime.now().strftime("%Y-%m-%d"),
    "ndvi": {
        **stats(ndvi),
        "vegetationRatio": round(float((ndvi[np.isfinite(ndvi)] > 0.3).mean()), 4),
        "image": "/data/NDVI.png",
    },
    "ndwi": {
        **stats(ndwi),
        "waterRatio": round(float((ndwi[np.isfinite(ndwi)] > 0.2).mean()), 4),
        "image": "/data/NDWI.png",
    },
    "timeseries": timeseries,
    "indices": indices,
    "atmosphere": atmosphere,
}

# 拷贝图片到前端
shutil.copy(RESULT / "NDVI.png", FRONTEND_DATA / "NDVI.png")
shutil.copy(RESULT / "NDWI.png", FRONTEND_DATA / "NDWI.png")
for _key in ("EVI", "NDBSI", "WET", "FVC", "LAI", "LST"):
    _p = RESULT / f"{_key}.png"
    if _p.exists():
        shutil.copy(_p, FRONTEND_DATA / f"{_key}.png")

with open(FRONTEND_DATA / "ndvi.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("已导出:", FRONTEND_DATA / "ndvi.json")
print("已拷贝:", FRONTEND_DATA / "NDVI.png", FRONTEND_DATA / "NDWI.png")
