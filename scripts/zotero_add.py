#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入本地文件到 Zotero 知识库（通过 Zotero 本地 API）

用途：
    把 PDF 等文件作为「父条目 + 附件」导入 Zotero 的指定分类，相当于
    把一份资料自动归档进知识库。

用法：
    python3 scripts/zotero_add.py <文件> --collection "FAE&Work/2- BMS/1- TI - BQ" \
        --kind Datasheet --title "BQ79616-Q1（SLUSD77）" [--tags BMS,TI] [--url ...]

    --collection 支持子目录路径（父/子/孙），每段精确优先、包含兜底；
    省略 --title 时用文件名（去扩展名）；--kind 按Wonder的命名规范加
    「[类型] 」前缀（类型词表见 docs/Zotero目录结构.md），标题已有 [ ] 前缀则不重复加。

分类纪律（重要）：
    - 只存入已存在的分类，脚本绝不自动创建
    - 目录结构如需调整，必须向 Wonder 提议并获同意
    - 找不到合适分类时报错并列出可选项，由 Simon 向 Wonder 提议新建

前置条件：
    1. Zotero 正在运行
    2. Zotero 设置 → 高级 → 已开启本地 API（允许 http://localhost:23119/api/）
    3. API key 存于 macOS 钥匙串（服务名 zotero-api-key）。
       若失效（撤销授权/换机），重新授权方法：
       先 POST http://localhost:23119/api/local/authorize 拿新 key（body 见
       README 或让 Simon 处理），再执行：
       security add-generic-password -a "Simon" -s "zotero-api-key" -w "<新key>"

实现说明：
    Zotero-Server-ID 每次从 API 响应头动态获取，无需配置。上传流程为
    五步：建父条目 → 建附件条目 → 申请上传 → 传文件 → 注册。
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.request

BASE = "http://localhost:23119/api/users/0"
KEYCHAIN_SERVICE = "zotero-api-key"
KEYCHAIN_ACCOUNT = "Simon"


def api_key():
    result = subprocess.run(
        ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit("❌ 钥匙串里没有 zotero-api-key，请先完成一次性授权（见文件头说明）")
    return result.stdout.strip()


class Zotero:
    def __init__(self):
        self.key = api_key()
        self.server_id = None

    def request(self, method, path, json_body=None, form=None, headers=None,
                raw_body=None, content_type=None):
        url = path if path.startswith("http") else BASE + path
        req = urllib.request.Request(url, method=method)
        req.add_header("Zotero-API-Key", self.key)
        if self.server_id:
            req.add_header("Zotero-Server-ID", self.server_id)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode()
            req.add_header("Content-Type", "application/json")
        elif form is not None:
            data = "&".join(f"{k}={v}" for k, v in form.items()).encode()
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
        elif raw_body is not None:
            data = raw_body
            if content_type:
                req.add_header("Content-Type", content_type)
        try:
            resp = urllib.request.urlopen(req, data, timeout=30)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            sys.exit(f"❌ API {method} {path} 失败 [{e.code}]: {body[:300]}")
        sid = resp.headers.get("Zotero-Server-ID")
        if sid:
            self.server_id = sid
        return resp, resp.read()

    def create_items(self, items):
        resp, body = self.request("POST", "/items", json_body=items)
        result = json.loads(body)
        batch = result.get("successful", result.get("success", {}))
        return {int(k): v["key"] for k, v in batch.items()}

    def upload_attachment(self, att_key, filepath):
        """五步上传流程的后三步：申请 → 传文件 → 注册"""
        with open(filepath, "rb") as f:
            content = f.read()
        md5 = hashlib.md5(content).hexdigest()
        payload = {
            "md5": md5,
            "filename": filepath.split("/")[-1],
            "filesize": len(content),
            "mtime": int(time.time() * 1000),
        }
        resp, body = self.request(
            "POST", f"/items/{att_key}/file", json_body=payload,
            headers={"If-None-Match": "*"},
        )
        info = json.loads(body)
        if "uploadKey" not in info:
            if info.get("exists") == "1":
                print("   （文件已存在，跳过上传）")
                return
            sys.exit(f"❌ 上传授权失败：{body[:300]}")

        # multipart 上传
        boundary = "----SimonZoteroBoundary"
        parts = []
        for name, value in (("uploadKey", info["uploadKey"]),
                            ("prefix", info.get("prefix", "")),
                            ("suffix", info.get("suffix", ""))):
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; "
                f'name="{name}"\r\n\r\n{value}\r\n'.encode()
            )
        parts.append(
            (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
             f"filename=\"{payload['filename']}\"\r\n"
             f"Content-Type: {info.get('contentType', 'application/octet-stream')}\r\n\r\n"
             ).encode() + content + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        resp, _ = self.request(
            "POST", info["url"], raw_body=b"".join(parts),
            content_type=f"multipart/form-data; boundary={boundary}",
        )
        if resp.status != 201:
            sys.exit(f"❌ 文件上传失败 [{resp.status}]")

        # 注册
        resp, _ = self.request(
            "POST", f"/items/{att_key}/file", form={"upload": info["uploadKey"]},
            headers={"If-None-Match": "*"},
        )
        if resp.status != 204:
            sys.exit(f"❌ 注册上传失败 [{resp.status}]")


def resolve_collection(z, path_spec):
    """按「父/子/孙」路径解析分类，返回 (collection, None) 或 (None, 错误信息)

    每段先精确匹配、再大小写不敏感包含匹配。找不到时给出当前层级可选清单，
    绝不自动创建分类（目录结构的改动必须经 Wonder 同意）。
    """
    _, body = z.request("GET", "/collections?format=json")
    collections = json.loads(body)
    children = {}
    for c in collections:
        # API 里根分类的 parentCollection 是 false，统一归一化为 None
        parent = c["data"].get("parentCollection") or None
        children.setdefault(parent, []).append(c)

    node = None
    candidates = children.get(None, [])
    for seg in path_spec.split("/"):
        seg = seg.strip()
        seg_l = seg.lower()
        exact = [c for c in candidates if c["data"]["name"].lower() == seg_l]
        fuzzy = [c for c in candidates if seg_l in c["data"]["name"].lower()]
        pick = exact or fuzzy
        if not pick:
            options = "、".join(sorted(c["data"]["name"] for c in candidates)) or "（无）"
            return None, f"路径段「{seg}」不存在。当前层级可选：{options}"
        node = pick[0]
        candidates = sorted(children.get(node["key"], []), key=lambda c: c["data"]["name"])

    hint = ""
    if candidates:
        hint = f"（注意：其下还有子分类 {'、'.join(c['data']['name'] for c in candidates)}，确认是否应放更深一层）"
    return (node, hint)


def main():
    parser = argparse.ArgumentParser(description="导入文件到 Zotero")
    parser.add_argument("file")
    parser.add_argument("--collection", required=True,
                        help='目标分类，支持子目录路径，如 "FAE&Work/2- BMS/1- TI - BQ"')
    parser.add_argument("--kind", default="",
                        help='资料类型前缀（命名规范），如 Datasheet / Application Note / Report，'
                             "自动生成「[类型] 标题」；标题里已有 [类型] 时不重复加")
    parser.add_argument("--title")
    parser.add_argument("--item-type", default="document")
    parser.add_argument("--tags", default="", help="逗号分隔")
    parser.add_argument("--url", default="")
    parser.add_argument("--date", default="")
    args = parser.parse_args()

    z = Zotero()

    # 按路径找分类（不自动创建——目录结构改动必须经 Wonder 同意）
    node, err = resolve_collection(z, args.collection)
    if err:
        sys.exit(f"❌ {err}\n（如确无合适分类，请向 Wonder 提议新建，不要自行创建）")
    print(f"（目标分类：{node['data']['name']}）")

    filename = args.file.split("/")[-1]
    title = args.title or filename.rsplit(".", 1)[0]
    if args.kind and not title.startswith("["):
        title = f"[{args.kind}] {title}"
    parent = {
        "itemType": args.item_type,
        "title": title,
        "collections": [node["key"]],
        "tags": [{"tag": t.strip()} for t in args.tags.split(",") if t.strip()],
    }
    if args.url:
        parent["url"] = args.url
    if args.date:
        parent["date"] = args.date

    idx = z.create_items([parent])
    pkey = idx[0]
    print(f"✅ 父条目已建：{title}（{pkey}）")

    att = {
        "itemType": "attachment",
        "linkMode": "imported_file",
        "filename": filename,
        "contentType": "application/pdf" if filename.lower().endswith(".pdf")
                       else "application/octet-stream",
        "parentItem": pkey,
    }
    idx = z.create_items([att])
    akey = idx[0]
    z.upload_attachment(akey, args.file)
    print(f"✅ 附件已上传：{filename}")
    print(f"📚 已导入 Zotero 分类「{args.collection}」")


if __name__ == "__main__":
    main()
