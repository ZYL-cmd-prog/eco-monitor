# -*- coding: utf-8 -*-
"""
alerts.py — 风险分级预警规则引擎（方案 A：定时生成 + 前端轮询）

从真实监测/遥感反演数据，按国标阈值 / 时序趋势生成分级预警，输出前端
「预警中心」Alerts.vue 和大屏「最新预警」需要的 alerts.json。

所有预警都由真实数据驱动；某类数据缺失时该类不产出预警（不造数、不冒充
真实监测）。分级：红 > 橙 > 黄 > 蓝。

数据源：
  - 大气：result/aqi.json（AQICN 监测站地面浓度，准实时，由 aqi.py 生成）
  - 水体/植被/生态：eco-monitor/public/data/ndvi.json（遥感反演，由 export_frontend.py 生成）

用法：
    python alerts.py                        # 默认读 result/aqi.json + public/data/ndvi.json
    python alerts.py <aqi.json> <ndvi.json>

输出：eco-monitor/public/data/alerts.json
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Windows 控制台默认 GBK，打印中文/特殊字符（如 μg/m³ 的 ³）会崩；统一按 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = Path(__file__).parent
FRONTEND_DATA = BASE.parent / "eco-monitor" / "public" / "data"
DEFAULT_AQI = BASE / "result" / "aqi.json"
DEFAULT_NDVI = FRONTEND_DATA / "ndvi.json"

SEVERITY = {"红色": 0, "橙色": 1, "黄色": 2, "蓝色": 3}


def load_json(path):
    if path is None or not Path(path).exists():
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"读取 {path} 失败：{e}")
        return None


def air_alerts(air):
    """AQICN 地面浓度 → 大气污染预警（GB3095-2012 二级限值，参考 HJ633 AQI 分级）。"""
    out = []
    if not air:
        return out
    t = air.get("time") or air.get("date") or ""
    area = "宜宾城区"

    def g(key):
        x = air.get(key) or {}
        return x.get("mean")

    def add(ind, val, unit, level, desc):
        out.append({
            "time": t, "area": area, "type": "大气污染", "level": level,
            "status": "待处理", "desc": desc, "indicator": ind,
            "value": val, "unit": unit, "source": "监测站",
        })

    aqi = g("aqi")
    pm25 = g("pm25")
    pm10 = g("pm10")
    so2 = g("so2")
    no2 = g("no2")
    o3 = g("o3")
    co = g("co")

    # AQI（HJ633）：>100 轻度、>150 中度、>200 重度
    if aqi is not None:
        if aqi > 200:
            add("AQI", aqi, "", "红色", f"空气质量指数 {aqi}（重度污染），阈值 200")
        elif aqi > 150:
            add("AQI", aqi, "", "橙色", f"空气质量指数 {aqi}（中度污染），阈值 150")
        elif aqi > 100:
            add("AQI", aqi, "", "黄色", f"空气质量指数 {aqi}（轻度污染），阈值 100")
    # PM2.5（24h 二级限值 75 μg/m³）
    if pm25 is not None:
        if pm25 > 150:
            add("PM2.5", pm25, "μg/m³", "红色", f"PM2.5 浓度 {pm25} μg/m³，严重超标（限值 75）")
        elif pm25 > 115:
            add("PM2.5", pm25, "μg/m³", "橙色", f"PM2.5 浓度 {pm25} μg/m³，超标（限值 75）")
        elif pm25 > 75:
            add("PM2.5", pm25, "μg/m³", "黄色", f"PM2.5 浓度 {pm25} μg/m³，超过二级限值 75")
    # PM10（24h 二级限值 150 μg/m³）
    if pm10 is not None:
        if pm10 > 350:
            add("PM10", pm10, "μg/m³", "红色", f"PM10 浓度 {pm10} μg/m³，严重超标（限值 150）")
        elif pm10 > 250:
            add("PM10", pm10, "μg/m³", "橙色", f"PM10 浓度 {pm10} μg/m³，超标（限值 150）")
        elif pm10 > 150:
            add("PM10", pm10, "μg/m³", "黄色", f"PM10 浓度 {pm10} μg/m³，超过二级限值 150")
    # NO2（24h 二级限值 80 μg/m³；1h 二级 200）
    if no2 is not None:
        if no2 > 200:
            add("NO2", no2, "μg/m³", "红色", f"NO2 浓度 {no2} μg/m³，严重超标（1h 限值 200）")
        elif no2 > 120:
            add("NO2", no2, "μg/m³", "橙色", f"NO2 浓度 {no2} μg/m³，超标")
        elif no2 > 80:
            add("NO2", no2, "μg/m³", "黄色", f"NO2 浓度 {no2} μg/m³，超过 24h 二级限值 80")
    # SO2（24h 二级限值 150 μg/m³；1h 二级 500）
    if so2 is not None:
        if so2 > 500:
            add("SO2", so2, "μg/m³", "橙色", f"SO2 浓度 {so2} μg/m³，超标（1h 限值 500）")
        elif so2 > 150:
            add("SO2", so2, "μg/m³", "黄色", f"SO2 浓度 {so2} μg/m³，超过 24h 二级限值 150")
    # O3（8h 二级限值 160 μg/m³）
    if o3 is not None:
        if o3 > 265:
            add("O3", o3, "μg/m³", "橙色", f"O3 浓度 {o3} μg/m³，超标（8h 限值 160）")
        elif o3 > 160:
            add("O3", o3, "μg/m³", "黄色", f"O3 浓度 {o3} μg/m³，超过 8h 二级限值 160")
    # CO（24h 二级限值 4 mg/m³）
    if co is not None:
        if co > 4:
            add("CO", co, "mg/m³", "黄色", f"CO 浓度 {co} mg/m³，超过 24h 二级限值 4")
    return out


def water_alerts(ndvi):
    """水体反演 → 富营养化 / 浑浊预警（FAI 正值=漂浮藻类；浑浊度经验阈值，待本地校准）。"""
    out = []
    if not ndvi:
        return out
    water = ndvi.get("water") or {}
    date = water.get("date") or ndvi.get("date") or ""
    fai = (water.get("fai") or {}).get("median")
    turb = (water.get("turbidity") or {}).get("median")

    if fai is not None and fai > 0:
        if fai > 0.1:
            level = "橙色"
        elif fai > 0.02:
            level = "黄色"
        else:
            level = "蓝色"
        out.append({
            "time": date, "area": "宜宾长江干流", "type": "水体富营养化", "level": level,
            "status": "待处理", "desc": f"浮游藻类指数 FAI={fai:.3f} 为正值，疑似藻类增殖",
            "indicator": "FAI", "value": round(fai, 4), "unit": "", "source": "遥感",
        })

    if turb is not None:
        if turb > 100:
            level = "红色"
        elif turb > 50:
            level = "橙色"
        elif turb > 30:
            level = "黄色"
        else:
            level = None
        if level:
            out.append({
                "time": date, "area": "宜宾长江干流", "type": "水体浑浊", "level": level,
                "status": "待处理", "desc": f"水体浑浊度 {turb:.1f} NTU，超过阈值 30",
                "indicator": "RGBT", "value": round(turb, 2), "unit": "NTU", "source": "遥感",
            })
    return out


def lst_alerts(ndvi):
    """地表温度 → 城市热岛预警（地表温度 > 40℃ 视为热岛明显）。"""
    if not ndvi:
        return []
    lst = (ndvi.get("indices") or {}).get("lst") or {}
    mean = lst.get("mean")
    if mean is None:
        return []
    date = lst.get("date") or ndvi.get("date") or ""
    if mean > 50:
        level = "红色"
    elif mean > 45:
        level = "橙色"
    elif mean > 40:
        level = "黄色"
    else:
        return []
    return [{
        "time": date, "area": "宜宾城区", "type": "高温热岛", "level": level,
        "status": "待处理", "desc": f"地表温度 {mean:.1f}℃，出现城市热岛效应",
        "indicator": "LST", "value": round(mean, 1), "unit": "°C", "source": "遥感",
    }]


def vegetation_alerts(ndvi):
    """植被退化预警：用长期 MODIS 历史做同比（同比降幅 >15%），避免季节波动误报。"""
    if not ndvi:
        return []
    hist = ndvi.get("modisHistory") or []
    pts = [(h.get("month"), h.get("ndvi")) for h in hist if h.get("ndvi") is not None]
    if len(pts) < 13:
        return []  # 不足一年，无法同比
    last_month, last_val = pts[-1]
    y, m = int(last_month[:4]), last_month[5:7]
    prev = next((v for (mm, v) in pts if mm == f"{y - 1}-{m}"), None)
    if prev is None or prev <= 0:
        return []
    drop = (prev - last_val) / prev
    if drop > 0.3:
        level = "橙色"
    elif drop > 0.15:
        level = "黄色"
    else:
        return []
    return [{
        "time": last_month, "area": "长江上游示范区", "type": "植被退化", "level": level,
        "status": "待处理",
        "desc": f"NDVI {last_val:.3f}，较去年同期 {prev:.3f} 下降 {drop * 100:.0f}%，建议生态修复核查",
        "indicator": "NDVI", "value": round(last_val, 4), "unit": "", "source": "遥感",
    }]


def main():
    aqi_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_AQI
    ndvi_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_NDVI

    air = load_json(aqi_path)
    ndvi = load_json(ndvi_path)

    alerts = air_alerts(air) + water_alerts(ndvi) + lst_alerts(ndvi) + vegetation_alerts(ndvi)
    # 先按时间倒序，再按级别稳定排序（红→橙→黄→蓝），同级内保留最新在前
    alerts.sort(key=lambda a: str(a["time"]), reverse=True)
    alerts.sort(key=lambda a: SEVERITY.get(a["level"], 9))

    out = {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "region": "宜宾市 · 长江上游示范区",
        "count": len(alerts),
        "alerts": alerts,
    }
    out_path = FRONTEND_DATA / "alerts.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已生成 {out_path}（{len(alerts)} 条预警）")
    for a in alerts:
        print(f"  [{a['level']}] {a['type']} · {a['area']} · {a['desc']}")


if __name__ == "__main__":
    main()
