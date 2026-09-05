#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simon 工作环境自检脚本

用途：
    启动时快速检查 CLAUDE.md 所描述的能力配置是否与事实一致：
    脚本是否齐全、密钥是否在钥匙串、路径是否存在、知识卡片清单
    是否与 docs/knowledge/ 实际文件一致、NDA 红线（gitignore）是否完好。

用法：
    python3 scripts/self_check.py

输出：
    逐项 ✅/❌；有 ❌ 时退出码为 1（方便 Simon 注意到并当场修复）。
    只检查密钥是否存在，绝不打印密钥内容。
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED_SCRIPTS = ["read_mail.py", "send_mail.py", "zotero_lib.py", "zotero_add.py", "self_check.py"]
KEYCHAIN = [("qq-mail", "QQ 邮箱授权码"), ("zotero-api-key", "Zotero API key")]
REQUIRED_PATHS = ["docs/knowledge", "data/datasheets", "CLAUDE.md", ".gitignore"]
KNOWLEDGE_DIR = os.path.join(ROOT, "docs", "knowledge")

failures = []


def check(ok, label, hint=""):
    mark = "✅" if ok else "❌"
    line = f"{mark} {label}"
    if not ok and hint:
        line += f"（{hint}）"
    print(line)
    if not ok:
        failures.append(label)


def keychain_exists(service):
    result = subprocess.run(
        ["security", "find-generic-password", "-s", service],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def card_names_in_claudemd():
    """从 CLAUDE.md 的「现有卡片：」行解析卡片名（去掉括号注释）"""
    with open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"现有卡片[：:](.+)", text)
    if not m:
        return None  # CLAUDE.md 里没写清单行
    names = []
    for part in m.group(1).split("、"):
        name = re.sub(r"（[^）]*）", "", part).strip()
        if name:
            names.append(name)
    return names


def main():
    print("=== Simon 环境自检 ===\n[1] 脚本齐全性")
    for s in REQUIRED_SCRIPTS:
        path = os.path.join(ROOT, "scripts", s)
        check(os.path.exists(path), f"scripts/{s}",
              "缺失！能力配置引用了它" if s != "self_check.py" else "缺失！")

    print("\n[2] 密钥（只验存在，不显示内容）")
    for service, label in KEYCHAIN:
        check(keychain_exists(service), f"钥匙串 {label}（{service}）", "丢失，需重新配置")

    print("\n[3] 关键路径")
    for p in REQUIRED_PATHS:
        check(os.path.exists(os.path.join(ROOT, p)), p, "不存在")

    print("\n[4] 知识卡片清单 vs 实际文件")
    listed = card_names_in_claudemd()
    actual = sorted(
        f[:-3] for f in os.listdir(KNOWLEDGE_DIR)
        if f.endswith(".md") and not f.startswith(".")
    ) if os.path.isdir(KNOWLEDGE_DIR) else []
    if listed is None:
        check(False, "CLAUDE.md 有「现有卡片」清单行", "未找到，需补写")
    else:
        missing_on_disk = [n for n in listed if n not in actual]
        unregistered = [n for n in actual if n not in listed]
        check(not missing_on_disk,
              "清单中的卡片都存在" + (f"，缺：{missing_on_disk}" if missing_on_disk else ""),
              "更新卡片或恢复文件")
        check(not unregistered,
              "没有未登记的卡片" + (f"，未登记：{unregistered}" if unregistered else ""),
              "把新卡片加进 CLAUDE.md 清单")

    print("\n[5] NDA 红线：gitignore")
    try:
        with open(os.path.join(ROOT, ".gitignore"), encoding="utf-8") as f:
            gi = f.read()
        check("data/datasheets" in gi, ".gitignore 排除了 data/datasheets/", "红线失效，立即修复！")
    except FileNotFoundError:
        check(False, ".gitignore 存在", "丢失，data/datasheets 可能被推上公开仓库")

    print("\n=== 结果 ===")
    if failures:
        print(f"❌ {len(failures)} 项异常：{failures}")
        sys.exit(1)
    print("✅ 全部通过")


if __name__ == "__main__":
    main()
