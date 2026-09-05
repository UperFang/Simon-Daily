#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 data/datasheets/ 本地缓存（原始文件以 Zotero 为唯一真相源）

规则：
    - 默认：删除「修改时间超过 N 天（默认 3 天）」且「已确认存在于 Zotero」的缓存文件
    - --force：不看时间，删除所有已确认存在于 Zotero 的缓存文件
    - --days N：自定义保留天数
    - 安全阀：Zotero 库中找不到同名文件的缓存一律保留并提示——绝不删除唯一副本

用法：
    python3 scripts/cleanup_cache.py [--days 3] [--force]

说明：
    由启动例程静默调用；只有发生实际删除时才需要在汇报中提及。
"""

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "data", "datasheets")
ZOTERO_STORAGE = os.path.expanduser("~/Zotero/storage")


def zotero_filenames():
    """收集 Zotero storage 里的全部附件文件名（一层 key 目录 + 文件名）"""
    names = set()
    if not os.path.isdir(ZOTERO_STORAGE):
        return names
    for key_dir in os.listdir(ZOTERO_STORAGE):
        subdir = os.path.join(ZOTERO_STORAGE, key_dir)
        if os.path.isdir(subdir):
            for f in os.listdir(subdir):
                names.add(f)
    return names


def main():
    parser = argparse.ArgumentParser(description="清理 datasheet 本地缓存")
    parser.add_argument("--days", type=int, default=3, help="保留最近 N 天（默认 3）")
    parser.add_argument("--force", action="store_true", help="不看时间，清掉所有已入 Zotero 的缓存")
    args = parser.parse_args()

    if not os.path.isdir(CACHE_DIR):
        print("（缓存目录不存在，无事可做）")
        return
    files = [f for f in os.listdir(CACHE_DIR)
             if os.path.isfile(os.path.join(CACHE_DIR, f)) and not f.startswith(".")]
    if not files:
        return  # 空缓存，静默退出

    known = zotero_filenames()
    now = time.time()
    deleted, kept_new, kept_unsafe = [], [], []

    for f in files:
        path = os.path.join(CACHE_DIR, f)
        if f not in known:
            kept_unsafe.append(f)  # Zotero 里没有，安全阀保留
            continue
        if args.force or (now - os.path.getmtime(path)) > args.days * 86400:
            os.remove(path)
            deleted.append(f)
        else:
            kept_new.append(f)

    for f in deleted:
        print(f"🗑 已清理缓存（Zotero 有正本）：{f}")
    for f in kept_unsafe:
        print(f"⚠️ 保留（Zotero 中未找到同名文件，请确认后手动处理）：{f}")
    if kept_new and not args.force:
        print(f"（{len(kept_new)} 个近期缓存保留：{', '.join(kept_new)}）")
    if not deleted and not kept_unsafe:
        print("（缓存均有效，无需清理）")


if __name__ == "__main__":
    main()
