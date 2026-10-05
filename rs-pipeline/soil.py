# -*- coding: utf-8 -*-
"""
土壤 pH 与有机质（SOM）：从全球土壤数据库 SoilGrids（ISRIC，250m）提取宜宾真实值。

- phh2o：土壤 pH（水浸提），存 pH×10
- soc：土壤有机碳含量，单位 dg/kg（0.1 g/kg）
- SOM（有机质）≈ SOC × 1.724（Van Bemmelen 换算系数）

数据是静态土壤图（非实时），但值是真实观测/插值结果。
输出 result/soil.json。
用法：python soil.py
"""
import json
import os
import tempfile
import urllib.request
import numpy as np
import rasterio
from pathlib import Path
from datetime import datetime

BBOX = [104.3, 28.4, 105.1, 29.0]

BASE = Path(__file__).parent
RESULT = BASE / "result"
RESULT.mkdir(exist_ok=True)


def fetch_coverage(prop):
    """WCS 拉取某属性 0-5cm 均值 GeoTIFF，返回 (array, nodata)。"""
    url = (f"https://maps.isric.org/mapserv?map=/map/{prop}.map"
           "&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage"
           f"&COVERAGEID={prop}_0-5cm_mean&FORMAT=GEOTIFF_INT16"
           f"&SUBSET=long({BBOX[0]},{BBOX[2]})&SUBSET=lat({BBOX[1]},{BBOX[3]})"
           "&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/4326")
    tmp = os.path.join(tempfile.gettempdir(), f"soil_{prop}.tif")
    urllib.request.urlretrieve(url, tmp)
    with rasterio.open(tmp) as src:
        arr = src.read(1).astype(np.float64)
        nodata = src.nodata
    os.remove(tmp)
    return arr, nodata


def stats(arr, nodata):
    """剔除 0（水体/无数据）与 nodata 后的统计。"""
    valid = np.isfinite(arr) & (arr != 0)
    if nodata is not None:
        valid &= (arr != nodata)
    v = arr[valid]
    return {
        "mean": round(float(v.mean()), 2),
        "min": round(float(v.min()), 2),
        "max": round(float(v.max()), 2),
        "pixels": int(v.size),
    }


ph_raw, ph_nodata = fetch_coverage("phh2o")
soc_raw, soc_nodata = fetch_coverage("soc")

ph = stats(ph_raw, ph_nodata)
soc = stats(soc_raw, soc_nodata)

# 单位换算
ph_value = ph["mean"] / 10.0          # 存储 pH×10 -> pH
soc_g_kg = soc["mean"] * 0.1          # dg/kg -> g/kg
som_g_kg = soc_g_kg * 1.724           # 有机碳 -> 有机质

out = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "source": "SoilGrids (ISRIC, 250m)",
    "ph": {
        "mean": round(ph_value, 1),
        "min": round(ph["min"] / 10.0, 1),
        "max": round(ph["max"] / 10.0, 1),
        "unit": "",
        "pixels": ph["pixels"],
    },
    "som": {
        "mean": round(som_g_kg, 1),
        "min": round(soc["min"] * 0.1 * 1.724, 1),
        "max": round(soc["max"] * 0.1 * 1.724, 1),
        "unit": "g/kg",
        "pixels": soc["pixels"],
        "soc_g_kg": round(soc_g_kg, 1),
    },
}

path = RESULT / "soil.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("已输出:", path)
print(json.dumps(out, ensure_ascii=False, indent=2))
