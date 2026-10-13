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
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

SITE_ID = os.environ["NETLIFY_SITE_ID"]
TOKEN = os.environ["NETLIFY_AUTH_TOKEN"]

DIST = Path(__file__).resolve().parent.parent / "eco-monitor" / "dist"
ZIP_PATH = Path(__file__).resolve().parent / "deploy.zip"


def _get(path):
    """带鉴权的 GET，返回解析后的 JSON；出错时打印 Netlify 返回的详细原因并抛出。"""
    req = urllib.request.Request(
        f"https://api.netlify.com/api/v1/{path}",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        _report(e)
        raise


def _report(e):
    try:
        detail = e.read().decode("utf-8", "replace")
        print(f"Netlify 返回错误 HTTP {e.code} {e.reason}")
        print(f"详细信息：{detail}")
    except Exception:
        print(f"Netlify 返回错误 HTTP {e.code} {e.reason}（无响应体）")


# 0) 部署前先查一下站点：确认 token 能访问这个站点、站点归属哪个账号。
#    若这里就 403，说明 token 对不上站点（账号/团队不对，或 token 权限不足）。
try:
    site = _get(f"sites/{SITE_ID}")
    print("站点名称：", site.get("name"))
    print("所属账号：", (site.get("account_slug") or site.get("account_name") or "未知"))
    print("站点 URL：", site.get("ssl_url") or site.get("url"))
except urllib.error.HTTPError:
    print(">>> 无法访问站点，说明 token 对该站点无权限或站点 ID 不对，请先修复 token 再重试。")
    raise

# 1) 用 zipfile 打成正斜杠路径（PowerShell Compress-Archive 会写成反斜杠，Netlify 上 404）
with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(DIST):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, DIST).replace(os.sep, "/")
            z.write(full, rel)

# 2) POST 上传部署
req = urllib.request.Request(
    f"https://api.netlify.com/api/v1/sites/{SITE_ID}/deploys",
    data=ZIP_PATH.read_bytes(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/zip"},
    method="POST",
)
try:
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read())
except urllib.error.HTTPError as e:
    _report(e)
    raise

print("deploy id:", body.get("id"))
print("state:", body.get("state"))
print("url:", body.get("ssl_url") or body.get("url"))
