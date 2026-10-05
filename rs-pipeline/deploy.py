# -*- coding: utf-8 -*-
"""
把 eco-monitor/dist 打包成 zip（正斜杠路径）并上传到 Netlify 部署。

环境变量：
    NETLIFY_SITE_ID     Netlify 站点 ID
    NETLIFY_AUTH_TOKEN  Netlify 访问令牌

用法：python deploy.py
"""
import json
import os
import urllib.request
import zipfile
from pathlib import Path

SITE_ID = os.environ["NETLIFY_SITE_ID"]
TOKEN = os.environ["NETLIFY_AUTH_TOKEN"]

DIST = Path(__file__).resolve().parent.parent / "eco-monitor" / "dist"
ZIP_PATH = Path(__file__).resolve().parent / "deploy.zip"

# 用 zipfile 打成正斜杠路径（PowerShell Compress-Archive 会写成反斜杠，Netlify 上 404）
with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(DIST):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, DIST).replace(os.sep, "/")
            z.write(full, rel)

req = urllib.request.Request(
    f"https://api.netlify.com/api/v1/sites/{SITE_ID}/deploys",
    data=ZIP_PATH.read_bytes(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/zip"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    body = json.loads(resp.read())
print("deploy id:", body.get("id"))
print("state:", body.get("state"))
print("url:", body.get("ssl_url") or body.get("url"))
