# -*- coding: utf-8 -*-
"""
uav.py — 「空」层：无人机精细观测接入（框架）

对应申报书 2.1「空—天—地」一体化观测中的无人机层，用于点/小范围精细观测：
  农村人居环境整治、农业面源污染巡查、河道漂浮物/岸线巡查、生态修复点位前后对比。

当前状态：框架已就绪，尚未接入真实无人机正射影像。
  - 真实无人机正射影像（Orthomosaic GeoTIFF + 外方位/处理报告）放入 data/uav/ 后，
    在 process_ortho() 中按需计算高分辨率指数（NDVI / 漂浮物 / 垃圾点识别等）。
  - 本脚本目前只生成演示样例 uav.json（demo=true，明确标注），供前端展示模块结构。

用法：python uav.py
输出：eco-monitor/public/data/uav.json
"""
import json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
FRONTEND_DATA = BASE.parent / "eco-monitor" / "public" / "data"
UAV_DATA = BASE / "data" / "uav"          # 真实无人机影像落盘目录（接入后启用）
UAV_DATA.mkdir(parents=True, exist_ok=True)


def process_ortho(ortho_path):
    """接入真实无人机正射影像后：计算高分辨率指数 / 巡查发现。

    目前为占位。真实接入时在此实现（rasterio 读取正射影像 ->
    高分辨率 NDVI / 水面漂浮物 / 垃圾堆放点识别等），并返回巡查记录列表。
    """
    return None


def demo_flights():
    """演示样例（占位数据，非真实巡查结果）。

    真实无人机正射影像接入后，由 process_ortho() 的产出替换本列表。
    """
    return [
        {"date": "待接入", "area": "长江上游示范区（示例点位）",
         "type": "人居环境整治巡查", "finding": "示例：待接入真实巡查结果", "status": "演示样例"},
        {"date": "待接入", "area": "长江上游示范区（示例点位）",
         "type": "河道漂浮物 / 岸线巡查", "finding": "示例：待接入真实巡查结果", "status": "演示样例"},
        {"date": "待接入", "area": "长江上游示范区（示例点位）",
         "type": "生态修复点位前后对比", "finding": "示例：待接入真实巡查结果", "status": "演示样例"},
    ]


def main():
    out = {
        "note": "无人机巡查模块（「空—天—地」之空层）。当前为演示样例，待接入真实无人机正射影像与巡查记录。",
        "demo": True,
        "generatedAt": datetime.now().strftime("%Y-%m-%d"),
        "flights": demo_flights(),
    }
    out_path = FRONTEND_DATA / "uav.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {out_path}（演示样例，demo=true）")


if __name__ == "__main__":
    main()
