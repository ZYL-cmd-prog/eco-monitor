# -*- coding: utf-8 -*-
"""
fetch_live_data.py — 从线上站点拉取当前已发布的 data/ 文件到本地 public/data/

用途：air-alerts 轻量工作流（每 N 小时只刷新大气 + 预警）无法运行完整遥感管线
（public/data/ 已 gitignore、CI 全新 checkout 里不存在这些文件），因此先从线上把
上一轮发布的所有数据文件（遥感 json/png、预测、预警）拉下来，再覆盖大气/预警后
重新构建部署，保证不会把影像/预测文件弄丢。

用法：
    python fetch_live_data.py [站点 base url]
    LIVE_SITE_URL 环境变量可覆盖，默认线上站点。
"""
import os
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).parent
FRONTEND_DATA = BASE.parent / "eco-monitor" / "public" / "data"
FRONTEND_DATA.mkdir(parents=True, exist_ok=True)

DEFAULT_URL = "https://stately-kelpie-a365b9.netlify.app"
BASE_URL = (os.environ.get("LIVE_SITE_URL") or (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL)).rstrip("/")

# 线上 /data/ 目录下已知的数据文件（与 export_frontend.py / baseline.py / alerts.py / uav.py 的产出对齐）
FILES = [
    "ndvi.json", "prediction.json", "uav.json", "alerts.json",
    "NDVI.png", "NDWI.png", "EVI.png", "FVC.png", "LAI.png", "LST.png", "NDBSI.png", "WET.png",
]


def main():
    print(f"从 {BASE_URL} 拉取线上数据到 {FRONTEND_DATA}")
    ok = 0
    for name in FILES:
        url = f"{BASE_URL}/data/{name}"
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = r.read()
            (FRONTEND_DATA / name).write_bytes(data)
            print(f"  已拉取 {name} ({len(data)} B)")
            ok += 1
        except Exception as e:
            print(f"  跳过 {name}：{e}")
    print(f"完成：{ok}/{len(FILES)} 个文件")


if __name__ == "__main__":
    main()
