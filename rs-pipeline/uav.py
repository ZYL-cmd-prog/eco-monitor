# -*- coding: utf-8 -*-
"""
uav.py — 「空」层：无人机精细观测接入（框架 + 演示样例）

对应申报书 2.1「空—天—地」一体化观测中的无人机层，用于点/小范围精细观测：
  农村人居环境整治、农业面源污染巡查、河道漂浮物/岸线巡查、生态修复点位前后对比。

当前状态：框架已就绪，尚未接入真实无人机正射影像。
  - 真实无人机正射影像（Orthomosaic GeoTIFF + 外方位/处理报告）放入 data/uav/ 后，
    在 process_ortho() 中按需计算高分辨率指数（NDVI / 漂浮物 / 垃圾点识别等）。
  - 本脚本目前生成完整的演示样例 uav.json（demo=true，明确标注），
    覆盖「统计概览 / 巡查任务看板 / 飞行路线示意 / 巡查发现 / 生态修复前后对比 / 巡查记录」，
    供前端展示模块结构，所有数据均为占位演示，非真实巡查结果。

用法：python uav.py
输出：eco-monitor/public/data/uav.json
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent
FRONTEND_DATA = BASE_DIR.parent / "eco-monitor" / "public" / "data"
UAV_DATA = BASE_DIR / "data" / "uav"          # 真实无人机影像落盘目录（接入后启用）
UAV_DATA.mkdir(parents=True, exist_ok=True)

TODAY = datetime.now().date()


def _d(days_ago):
    return (TODAY - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def process_ortho(ortho_path):
    """接入真实无人机正射影像后：计算高分辨率指数 / 巡查发现。

    目前为占位。真实接入时在此实现（rasterio 读取正射影像 ->
    高分辨率 NDVI / 水面漂浮物 / 垃圾堆放点识别等），并返回巡查记录列表。
    """
    return None


def demo_summary():
    """演示统计概览（占位数据）。"""
    return {"flights": 12, "coverage": 8.6, "findings": 5, "rectified": 3}


def demo_tasks():
    """巡查任务看板（占位数据，非真实任务）。"""
    return [
        {"id": "UAV-2026-1013", "name": "长江干流河道漂浮物专项", "area": "宜宾·长江上游示范区",
         "type": "河道漂浮物 / 岸线", "status": "执行中", "progress": 60, "date": _d(0)},
        {"id": "UAV-2026-1012", "name": "农村人居环境整治巡查", "area": "示范区内某行政村",
         "type": "人居环境整治", "status": "待执行", "progress": 0, "date": _d(1)},
        {"id": "UAV-2026-1010", "name": "消落带植被修复点复查", "area": "长江消落带",
         "type": "生态修复前后对比", "status": "已完成", "progress": 100, "date": _d(3)},
        {"id": "UAV-2026-1008", "name": "农业面源污染巡查", "area": "示范区农田区",
         "type": "农业面源污染", "status": "已完成", "progress": 100, "date": _d(5)},
        {"id": "UAV-2026-1006", "name": "岸线违规堆放排查", "area": "长江左岸某段",
         "type": "河道漂浮物 / 岸线", "status": "已完成", "progress": 100, "date": _d(7)},
    ]


def demo_route():
    """飞行路线示意（占位航点，非真实航线）。"""
    waypoints = [
        [104.608, 28.742], [104.618, 28.748], [104.628, 28.752],
        [104.636, 28.750], [104.634, 28.742], [104.624, 28.736],
        [104.612, 28.738], [104.608, 28.742],
    ]
    return {"waypoints": waypoints, "start": "起降点", "lengthKm": 5.2,
            "area": "宜宾·长江上游示范区（示例航线）"}


def demo_findings():
    """巡查发现（占位数据，非真实发现）。"""
    return [
        {"level": "橙色", "type": "河道漂浮物", "area": "长江干流某段", "time": _d(0),
         "status": "处理中", "desc": "示例：疑似漂浮物聚集，待人工复核"},
        {"level": "黄色", "type": "农村生活垃圾堆放", "area": "示范区内某行政村", "time": _d(1),
         "status": "待处理", "desc": "示例：路边垃圾堆放点，建议限期清理"},
        {"level": "蓝色", "type": "岸线违规种植", "area": "长江左岸某段", "time": _d(3),
         "status": "已整改", "desc": "示例：消落带违规种植，已清理"},
        {"level": "黄色", "type": "农业面源污染", "area": "示范区农田区", "time": _d(5),
         "status": "已整改", "desc": "示例：疑似农药瓶乱弃，已处置"},
        {"level": "蓝色", "type": "生态修复点位", "area": "长江消落带", "time": _d(7),
         "status": "已整改", "desc": "示例：修复点位植被长势良好"},
    ]


def demo_restoration():
    """生态修复点位前后对比（占位数据）。"""
    return [
        {"point": "消落带植被修复点", "before": "NDVI 0.32", "after": "NDVI 0.58",
         "change": "+81%", "note": "示例：消落带复绿，前后对比待接入真实影像"},
        {"point": "岸线湿地修复点", "before": "湿地面积 1.2 亩", "after": "湿地面积 2.0 亩",
         "change": "+67%", "note": "示例：岸线湿地恢复，前后对比待接入真实影像"},
        {"point": "矿山迹地修复点", "before": "NDVI 0.21", "after": "NDVI 0.46",
         "change": "+119%", "note": "示例：矿山迹地复绿，前后对比待接入真实影像"},
    ]


def demo_flights():
    """巡查记录（占位数据，非真实巡查结果）。"""
    return [
        {"date": _d(0), "area": "宜宾·长江上游示范区", "type": "河道漂浮物 / 岸线巡查",
         "finding": "示例：发现疑似漂浮物聚集 1 处", "status": "演示样例"},
        {"date": _d(3), "area": "长江消落带", "type": "生态修复点位前后对比",
         "finding": "示例：修复点位植被长势良好", "status": "演示样例"},
        {"date": _d(5), "area": "示范区农田区", "type": "农业面源污染巡查",
         "finding": "示例：疑似农药瓶乱弃 1 处", "status": "演示样例"},
    ]


def main():
    out = {
        "note": "无人机巡查模块（「空—天—地」之空层）。当前为演示样例，待接入真实无人机正射影像与巡查记录。",
        "demo": True,
        "generatedAt": TODAY.strftime("%Y-%m-%d"),
        "summary": demo_summary(),
        "route": demo_route(),
        "tasks": demo_tasks(),
        "findings": demo_findings(),
        "restoration": demo_restoration(),
        "flights": demo_flights(),
    }
    out_path = FRONTEND_DATA / "uav.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {out_path}（演示样例，demo=true）")


if __name__ == "__main__":
    main()
