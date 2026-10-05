# -*- coding: utf-8 -*-
"""
Sentinel-5P (TROPOMI) 大气污染物柱浓度实算：NO2 / SO2 / O3。

数据源：Planetary Computer 集合 `sentinel-5p-l2-netcdf`（每轨按污染物拆成独立 item，
单个资产为 NetCDF，键分别为 no2 / so2 / o3）。TROPOMI 给出的是「柱浓度」（单位 mol/m²），
不是地面 μg/m³ 浓度，因此这里按柱浓度展示：
  - NO2  对流层柱浓度  mol/m² -> μmol/m²
  - SO2  总柱浓度      mol/m² -> μmol/m²
  - O3   总柱浓度      mol/m² -> DU（Dobson 单位）

稳健统计：先按物理范围裁剪剔除检索离群值（SO2 会有大量负值/伪影），再取中位数。
qa_value==0 视为无误差；若最近一轨无有效像元，往前回溯多轨直到找到有效值。

输出 result/s5p.json。
用法：python s5p.py
"""
import json
import os
import tempfile
import urllib.request
import numpy as np
import netCDF4
import planetary_computer
import pystac_client
from pathlib import Path
from datetime import datetime, timedelta

BBOX = [104.3, 28.4, 105.1, 29.0]

BASE = Path(__file__).parent
RESULT = BASE / "result"
RESULT.mkdir(exist_ok=True)

DU_PER_MOL_M2 = 2241.5  # 1 mol/m² = 2241.5 DU
MAX_ATTEMPTS = 5        # 每污染物最多回溯的轨道数

# 各污染物：资产键 / NetCDF 主变量 / 换算 / 物理裁剪范围(mol/m²) / qa_good
# 注意：O3 的 qa_value 语义与 NO2/SO2 相反——O3 用 1 表示有效、0 表示无效。
POLLUTANTS = {
    "no2": {
        "var": "nitrogendioxide_tropospheric_column",
        "unit": "μmol/m²",
        "scale": 1e6,
        "round": 1,
        "clip": (0.0, 5e-4),     # 0 ~ 500 μmol/m²
        "qa_good": 0,
    },
    "so2": {
        "var": "sulfurdioxide_total_vertical_column",
        "unit": "μmol/m²",
        "scale": 1e6,
        "round": 2,
        # SO2 NRTI 检索噪声大（大量负值+极端离群），对称裁剪只剔 ±2000 离群、
        # 保留噪声中心，再取中位数反映「背景/低于检测限」水平
        "clip": (-2e-3, 2e-3),
        "qa_good": 0,
        "floor": 0.0,            # 中位数若为负（低于检测限）按 0 计
    },
    "o3": {
        "var": "ozone_total_vertical_column",
        "unit": "DU",
        "scale": DU_PER_MOL_M2,
        "round": 0,
        "clip": (0.05, 0.25),    # 112 ~ 560 DU（总臭氧）
        "qa_good": 1,            # O3 有效像元 qa_value==1
    },
}

FILL = 9.96921e36

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

_end = datetime.utcnow()
_start = _end - timedelta(days=30)
search = catalog.search(
    collections=["sentinel-5p-l2-netcdf"],
    bbox=BBOX,
    datetime=f"{_start.date().isoformat()}/{_end.date().isoformat()}",
    limit=500,
)
items = list(search.item_collection())
print(f"30 天内共 {len(items)} 个 TROPOMI item")


def extract(key, spec):
    """取最近一轨（无效则回溯）下载并统计宜宾范围内的柱浓度。"""
    matched = sorted(
        [it for it in items if key in it.assets],
        key=lambda x: x.datetime, reverse=True,
    )
    if not matched:
        print(f"  {key}: 30 天内无影像")
        return None

    for item in matched[:MAX_ATTEMPTS]:
        href = item.assets[key].href
        tmp = os.path.join(tempfile.gettempdir(), f"s5p_{key}.nc")
        ok = False
        for _ in range(2):  # 下载失败重试一次
            try:
                urllib.request.urlretrieve(href, tmp)
                ok = True
                break
            except Exception as e:
                print(f"  {key}: 下载失败({type(e).__name__})，重试")
                if os.path.exists(tmp):
                    os.remove(tmp)
        if not ok:
            continue
        try:
            ds = netCDF4.Dataset(tmp)
            var_name = spec["var"]
            if var_name not in ds["/PRODUCT"].variables:
                print(f"  {key}: 变量 {var_name} 不存在")
                ds.close()
                os.remove(tmp)
                return None
            lat = ds["/PRODUCT/latitude"][0].astype(np.float64)
            lon = ds["/PRODUCT/longitude"][0].astype(np.float64)
            qa = ds["/PRODUCT/qa_value"][0].astype(np.int32)
            var = ds["/PRODUCT"][var_name][0].astype(np.float64)
            ds.close()
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

        # 掩膜：宜宾 bbox + 质量好 + 有效值 + 非填充
        valid = (
            (lat >= BBOX[1]) & (lat <= BBOX[3]) &
            (lon >= BBOX[0]) & (lon <= BBOX[2]) &
            (qa == spec["qa_good"]) &
            np.isfinite(var) & (var < FILL * 0.1)
        )
        vals = var[valid]
        # 物理范围裁剪（剔除 SO2 负值等检索伪影）
        lo, hi = spec["clip"]
        vals = vals[(vals >= lo) & (vals <= hi)]
        if vals.size < 5:
            print(f"  {key}: 轨 {item.id[-10:]} 宜宾有效像元 {vals.size}（回溯下一轨）")
            continue

        s = spec["scale"]
        r = spec["round"]
        floor = spec.get("floor")
        med = float(np.median(vals))
        mean = float(vals.mean())
        if floor is not None:
            med = max(med, floor)
            mean = max(mean, floor)
        print(f"  {key}: {item.id}  日期 {item.datetime.date()}  有效像元 {vals.size}")
        return {
            "median": round(med * s, r),
            "mean": round(mean * s, r),
            "p10": round(float(np.percentile(vals, 10)) * s, r),
            "p90": round(float(np.percentile(vals, 90)) * s, r),
            "unit": spec["unit"],
            "pixels": int(vals.size),
            "date": item.datetime.date().isoformat(),
            "scene_id": item.id,
        }

    print(f"  {key}: {MAX_ATTEMPTS} 轨内均无足够有效像元")
    return None


out = {}
for key, spec in POLLUTANTS.items():
    out[key] = extract(key, spec)

dates = [v["date"] for v in out.values() if v]
out["date"] = max(dates) if dates else None

path = RESULT / "s5p.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("已输出:", path)
print(json.dumps(out, ensure_ascii=False, indent=2))
