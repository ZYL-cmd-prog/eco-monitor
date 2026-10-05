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


out = {
    "date": (d.get("time", {}).get("s") or "")[:10],
    "source": f"AQICN 监测站（{d.get('city', {}).get('name', '宜宾')}）",
    "aqi": {"mean": d.get("aqi"), "unit": ""},
    "pm25": {"mean": v("pm25"), "unit": "μg/m³"},
    "pm10": {"mean": v("pm10"), "unit": "μg/m³"},
    "so2": {"mean": v("so2"), "unit": "μg/m³"},
    "no2": {"mean": v("no2"), "unit": "μg/m³"},
    "o3": {"mean": v("o3"), "unit": "μg/m³"},
    "co": {"mean": v("co"), "unit": "mg/m³"},
}

path = RESULT / "aqi.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("已输出:", path)
print(json.dumps(out, ensure_ascii=False, indent=2))
