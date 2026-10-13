# -*- coding: utf-8 -*-
"""
空气质量监测站数据：AQI + PM2.5/PM10/SO2/NO2/O3/CO 地面浓度。

数据源：AQICN（World Air Quality Index，聚合中国环境监测总站各城市监测站数据）。
用宜宾市中心坐标 geo:28.75;104.62 取最近监测站。

token 从环境变量 AQICN_TOKEN 读取；未配置则跳过（前端退回卫星柱浓度/演示）。
注册免费 token：https://aqicn.org/data-platform/token/

输出 result/aqi.json。
用法：python aqi.py
"""
import json
import os
import urllib.request
from pathlib import Path

BASE = Path(__file__).parent
RESULT = BASE / "result"
RESULT.mkdir(exist_ok=True)

TOKEN = os.environ.get("AQICN_TOKEN", "").strip()
FEED = "geo:28.75;104.62"   # 宜宾市中心

if not TOKEN:
    print("未设置 AQICN_TOKEN，跳过空气质量监测站数据。")
    raise SystemExit(0)

url = f"https://api.waqi.info/feed/{FEED}/?token={TOKEN}"
with urllib.request.urlopen(url, timeout=30) as r:
    data = json.loads(r.read().decode("utf-8"))

if data.get("status") != "ok":
    print("AQICN 返回异常:", json.dumps(data.get("data"), ensure_ascii=False))
    raise SystemExit(1)

d = data["data"]
iaqi = d.get("iaqi", {})


def v(key):
    x = iaqi.get(key)
    return x.get("v") if x else None


# 附近监测站列表（AQICN map/bounds），用于大屏「站点分布」真实点位
STATIONS_BBOX = "26,102,31,108"   # 川南 / 渝西 / 黔北（长江上游）
stations = []
try:
    surl = f"https://api.waqi.info/map/bounds/?latlng={STATIONS_BBOX}&token={TOKEN}"
    with urllib.request.urlopen(surl, timeout=30) as r:
        sdata = json.loads(r.read().decode("utf-8"))
    if sdata.get("status") == "ok":
        seen = set()
        for s in sdata.get("data", []):
            name = (s.get("station") or {}).get("name")
            geo = (s.get("station") or {}).get("geo")
            if not name or not geo or len(geo) < 2 or name in seen:
                continue
            seen.add(name)
            try:
                aqi_v = int(s.get("aqi"))
            except (TypeError, ValueError):
                aqi_v = None
            stations.append({"name": name, "lat": float(geo[0]), "lon": float(geo[1]), "aqi": aqi_v})
    stations = stations[:40]
    print(f"获取到 {len(stations)} 个监测站")
except Exception as e:
    print("监测站列表获取失败（跳过）：", e)


out = {
    "time": d.get("time", {}).get("s") or "",
    "date": (d.get("time", {}).get("s") or "")[:10],
    "source": f"AQICN 监测站（{d.get('city', {}).get('name', '宜宾')}）",
    "aqi": {"mean": d.get("aqi"), "unit": ""},
    "pm25": {"mean": v("pm25"), "unit": "μg/m³"},
    "pm10": {"mean": v("pm10"), "unit": "μg/m³"},
    "so2": {"mean": v("so2"), "unit": "μg/m³"},
    "no2": {"mean": v("no2"), "unit": "μg/m³"},
    "o3": {"mean": v("o3"), "unit": "μg/m³"},
    "co": {"mean": v("co"), "unit": "mg/m³"},
    "stations": stations,
}

path = RESULT / "aqi.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("已输出:", path)
print(json.dumps(out, ensure_ascii=False, indent=2))

# 同步到前端 ndvi.json（若存在），让指标页/预警的空气数据保持一致（air-alerts 轻量工作流用）
_ndvi = BASE.parent / "eco-monitor" / "public" / "data" / "ndvi.json"
if _ndvi.exists():
    _d = json.loads(_ndvi.read_text(encoding="utf-8"))
    _d["air"] = out
    _d["stations"] = stations
    _ndvi.write_text(json.dumps(_d, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已同步空气数据 + 站点到:", _ndvi)
