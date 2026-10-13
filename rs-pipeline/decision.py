# -*- coding: utf-8 -*-
"""
decision.py — 治理决策 / 辅助决策规则引擎（文档 2.4「辅助决策」、创新点(3)「观测-计算-诊断-预警-决策」的最后一环）

从真实预警（alerts.json）联动生成分级处置方案，并从遥感反演（ndvi.json）生成五维常态治理建议。
纯规则映射、不造数；某类数据缺失时该类不产出建议。

输入：
  - eco-monitor/public/data/alerts.json（alerts.py 生成）
  - eco-monitor/public/data/ndvi.json（export_frontend.py 生成）
输出：eco-monitor/public/data/decision.json
用法：python decision.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = Path(__file__).parent
FRONTEND_DATA = BASE.parent / "eco-monitor" / "public" / "data"

# 预警等级 → (优先级, 处置时限)
LEVEL_PRIORITY = {
    "红色": ("高", "立即处置"),
    "橙色": ("高", "12 小时内"),
    "黄色": ("中", "24 小时内"),
    "蓝色": ("低", "48 小时内"),
}

# 指标 → (类别, 处置措施, 责任部门)。指标名与 alerts.py 一致。
INDICATOR_RULES = {
    "AQI": ("大气环境", ["启动区域应急响应，加强工业源与移动源协同管控", "发布健康防护提示，引导减少户外活动"], "市生态环境局"),
    "PM2.5": ("大气环境", ["加强建筑工地与道路扬尘管控，增加洒水降尘频次", "督促重点工业企业错峰生产、限产减排", "加强秸秆禁烧与露天焚烧巡查"], "市生态环境局"),
    "PM10": ("大气环境", ["加强渣土运输车辆密闭监管，落实裸土覆盖", "强化施工工地围挡与喷淋降尘"], "市生态环境局"),
    "NO2": ("大气环境", ["加强机动车尾气治理，优化重点路段交通疏导", "排查非道路移动机械排放"], "市生态环境局"),
    "SO2": ("大气环境", ["排查燃煤锅炉与散煤使用，督促脱硫设施稳定运行"], "市生态环境局"),
    "O3": ("大气环境", ["管控挥发性有机物（VOCs）排放，高温时段错峰喷涂作业", "加强加油站油气回收与有机溶剂使用监管"], "市生态环境局"),
    "CO": ("大气环境", ["排查不完全燃烧源，管控散煤与露天焚烧"], "市生态环境局"),
    "FAI": ("水体环境", ["加强藻类巡查与打捞，实施生态调水抑藻", "排查入河污染负荷，控制氮磷输入"], "市生态环境局、市水务局"),
    "RGBT": ("水体环境", ["排查上游施工排泥与水土流失，加强水土保持", "强化入河排污口监管与清淤"], "市水务局"),
    "LST": ("生态热岛", ["增加城市绿地与透水铺装，降低地表温度", "推广屋顶绿化与建筑遮阳，缓解热岛效应"], "市住建局、市城管局"),
    "NDVI": ("植被生态", ["排查违规占用与破坏植被行为，依法查处", "启动生态修复与补植补造，恢复植被覆盖"], "市林业局、市自然资源局"),
}
DEFAULT_RULE = ("综合", ["组织现场核查，按职责分工落实整改"], "市生态环境局")


def load_json(path):
    if not Path(path).exists():
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"读取 {path} 失败：{e}")
        return None


def num(d, *keys):
    """取第一个非空数值，兼容 mean/median 两种字段。"""
    for k in keys:
        v = (d or {}).get(k)
        if v is not None:
            return v
    return None


def build_actions(alerts):
    actions = []
    for a in alerts:
        ind = a.get("indicator") or ""
        cat, measures, resp = INDICATOR_RULES.get(ind, DEFAULT_RULE)
        prio, deadline = LEVEL_PRIORITY.get(a.get("level"), ("中", "24 小时内"))
        actions.append({
            "priority": prio,
            "category": cat,
            "level": a.get("level"),
            "trigger": a.get("desc") or f"{ind} 预警",
            "measures": measures,
            "responsible": resp,
            "deadline": deadline,
        })
    order = {"高": 0, "中": 1, "低": 2}
    actions.sort(key=lambda x: order.get(x["priority"], 3))
    return actions


def build_dimensions(d):
    dims = []
    air = d.get("air") or {}
    water = d.get("water") or {}
    soil = d.get("soil") or {}
    indices = d.get("indices") or {}
    mh = d.get("modisHistory") or []

    # 大气
    pm25 = num(air.get("pm25"))
    if pm25 is None:
        dims.append({"name": "大气环境", "signal": "数据待接入", "status": "—", "suggestion": "接入监测站数据后自动生成建议"})
    elif pm25 > 75:
        dims.append({"name": "大气环境", "signal": f"PM2.5 {pm25:.0f} μg/m³", "status": "需治理", "suggestion": "PM2.5 超标，加强扬尘与工业源管控"})
    elif pm25 > 35:
        dims.append({"name": "大气环境", "signal": f"PM2.5 {pm25:.0f} μg/m³", "status": "保持监测", "suggestion": "空气质量良，保持常态监测与污染源监管"})
    else:
        dims.append({"name": "大气环境", "signal": f"PM2.5 {pm25:.0f} μg/m³", "status": "状况良好", "suggestion": "空气质量优，保持现状"})

    # 水体
    fai = num(water.get("fai"), "median", "mean")
    turb = num(water.get("turbidity"), "median", "mean")
    if fai is None and turb is None:
        dims.append({"name": "水体环境", "signal": "数据待接入", "status": "—", "suggestion": "接入水体反演数据后自动生成建议"})
    elif (fai is not None and fai > 0) or (turb is not None and turb > 30):
        sig = f"FAI {fai:.3f}" if fai is not None and fai > 0 else f"浑浊度 {turb:.0f} NTU"
        dims.append({"name": "水体环境", "signal": sig, "status": "需治理", "suggestion": "存在藻类/浑浊风险，加强水体巡查与生态调水"})
    else:
        dims.append({"name": "水体环境", "signal": "FAI / 浑浊度正常", "status": "状况良好", "suggestion": "水体状况正常，保持常态监测"})

    # 土壤
    sqi = num(soil.get("sqi"))
    if sqi is None:
        dims.append({"name": "土壤环境", "signal": "数据待接入", "status": "—", "suggestion": "接入土壤数据后自动生成建议"})
    else:
        dims.append({"name": "土壤环境", "signal": f"SQI {sqi:.2f}", "status": "状况良好", "suggestion": "土壤质量整体良好，保持化肥减量与面源污染管控"})

    # 植被（NDVI 同比）
    ndvi_signal, ndvi_status, ndvi_sug = "数据待接入", "—", "接入长期时序数据后自动生成建议"
    if len(mh) >= 13:
        cur = mh[-1].get("ndvi")
        prev = mh[-13].get("ndvi")   # 去年同期
        if cur is not None and prev is not None and prev != 0:
            delta = (cur - prev) / prev * 100
            ndvi_signal = f"NDVI 同比 {delta:+.1f}%"
            if delta < -15:
                ndvi_status, ndvi_sug = "需治理", "植被同比明显退化，排查破坏行为并启动生态修复"
            elif delta < 0:
                ndvi_status, ndvi_sug = "保持监测", "植被同比小幅下降，持续监测变化趋势"
            else:
                ndvi_status, ndvi_sug = "状况良好", "植被长势同比稳定或向好，保持常态管护"
    elif mh:
        ndvi_signal = f"NDVI {mh[-1].get('ndvi', 0):.3f}"
        ndvi_status, ndvi_sug = "保持监测", "长期时序数据积累中，持续监测植被变化"
    dims.append({"name": "植被生态", "signal": ndvi_signal, "status": ndvi_status, "suggestion": ndvi_sug})

    # 生态（热岛 LST）
    lst = num(indices.get("lst"))
    if lst is None:
        dims.append({"name": "生态热岛", "signal": "数据待接入", "status": "—", "suggestion": "接入地表温度数据后自动生成建议"})
    elif lst > 38:
        dims.append({"name": "生态热岛", "signal": f"LST {lst:.1f} ℃", "status": "需治理", "suggestion": "热岛效应明显，增加绿地与透水铺装"})
    else:
        dims.append({"name": "生态热岛", "signal": f"LST {lst:.1f} ℃", "status": "状况良好", "suggestion": "地表温度正常，保持生态空间管控"})

    return dims


def make_summary(alerts):
    if not alerts:
        return "当前无预警事件，生态环境总体平稳，保持常态监测与预防性治理。"
    levels = [a.get("level") for a in alerts]
    if "红色" in levels:
        return "存在重大生态环境风险，需立即启动应急响应，多部门联动处置。"
    if "橙色" in levels:
        return "生态环境风险较高，需优先处置重点问题，并加强巡查频次。"
    if "黄色" in levels:
        return "存在局部生态环境问题，按预警分级开展针对性治理。"
    return "生态环境基本平稳，存在轻微风险，需持续关注。"


def main():
    alerts_json = load_json(FRONTEND_DATA / "alerts.json")
    ndvi_json = load_json(FRONTEND_DATA / "ndvi.json")

    alerts = (alerts_json or {}).get("alerts") or []
    region = (ndvi_json or {}).get("region") or "宜宾市 · 长江上游示范区"

    out = {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "region": region,
        "summary": make_summary(alerts),
        "actions": build_actions(alerts),
        "dimensions": build_dimensions(ndvi_json or {}),
    }
    out_path = FRONTEND_DATA / "decision.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {out_path}：{len(out['actions'])} 条处置动作，{len(out['dimensions'])} 个维度建议")


if __name__ == "__main__":
    main()
