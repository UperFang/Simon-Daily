#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取本地 Zotero 文献库：列出条目、搜索、浏览分类、定位原文附件

用途：
    Simon 的本地知识库入口。Zotero 的元数据存在 ~/Zotero/zotero.sqlite（SQLite），
    原文附件存在 ~/Zotero/storage/<8位key>/ 里。本脚本用"只读快照"方式查询，
    Zotero 开着也没关系，不会锁定或修改数据库。

用法：
    python3 scripts/zotero_lib.py                # 列出最近 20 个条目
    python3 scripts/zotero_lib.py 50             # 列出最近 50 个条目
    python3 scripts/zotero_lib.py -s 关键词       # 按标题/作者搜索（附原文路径）
    python3 scripts/zotero_lib.py --collections  # 列出所有分类及条目数
    python3 scripts/zotero_lib.py -c "分类名"     # 浏览某个分类下的条目（附原文路径）

输出说明：
    条目格式为 [序号] 标题 —— 作者 (年份)，搜索/分类模式下还会给出 📄 原文绝对路径，
    用 Read 工具（或 open 命令）即可直接打开原文件（PDF 等）。
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ZOTERO_DIR = os.path.expanduser("~/Zotero")
DB_PATH = os.path.join(ZOTERO_DIR, "zotero.sqlite")
STORAGE_DIR = os.path.join(ZOTERO_DIR, "storage")


def snapshot_db():
    """直接复制数据库文件做快照（纯文件操作，不碰 Zotero 的锁，秒级完成）"""
    if not os.path.exists(DB_PATH):
        sys.exit(f"❌ 未找到 Zotero 数据库：{DB_PATH}")
    fd, tmp = tempfile.mkstemp(suffix=".sqlite", prefix="zotero_snap_")
    os.close(fd)
    shutil.copy2(DB_PATH, tmp)
    # WAL/SHM 一并复制，打开快照时才能重放未合并的写入，保证数据一致
    for suffix in ("-wal", "-shm"):
        src = DB_PATH + suffix
        if os.path.exists(src):
            shutil.copy2(src, tmp + suffix)
    return tmp


def cleanup_snapshot(tmp):
    for suffix in ("", "-wal", "-shm"):
        path = tmp + suffix
        if os.path.exists(path):
            os.remove(path)


def q(db, sql, args=()):
    return db.execute(sql, args).fetchall()


def item_field(db, item_id, field):
    """取条目某个字段的值（title/date 等）"""
    rows = q(
        db,
        "SELECT idv.value FROM itemData id "
        "JOIN fields f ON f.fieldID = id.fieldID AND f.fieldName = ? "
        "JOIN itemDataValues idv ON idv.valueID = id.valueID "
        "WHERE id.itemID = ?",
        (field, item_id),
    )
    return rows[0][0] if rows else ""


def item_creators(db, item_id, max_n=3):
    rows = q(
        db,
        "SELECT c.firstName, c.lastName FROM itemCreators ic "
        "JOIN creators c ON c.creatorID = ic.creatorID "
        "WHERE ic.itemID = ? ORDER BY ic.orderIndex LIMIT ?",
        (item_id, max_n),
    )
    names = [(f"{ln} {fn}".strip() if fn else ln) for fn, ln in rows]
    return names


def attachment_paths(db, item_id):
    """返回条目下所有原文附件的绝对路径（storage: 相对路径换算成实际位置）"""
    rows = q(
        db,
        "SELECT a.path, a.linkMode, i.key FROM itemAttachments a "
        "JOIN items i ON i.itemID = a.itemID "
        "WHERE a.parentItemID = ?",
        (item_id,),
    )
    paths = []
    for path, link_mode, key in rows:
        if not path:
            continue
        if path.startswith("storage:"):
            paths.append(os.path.join(STORAGE_DIR, key, path[len("storage:"):]))
        elif path.startswith("attachments:"):
            paths.append(os.path.join(ZOTERO_DIR, path))
        elif os.path.isabs(path) and os.path.exists(path):
            paths.append(path)  # 链接的本地文件
    return [p for p in paths if os.path.exists(p)]


def base_query(where="", tail="", args=()):
    return (
        "SELECT i.itemID, it.typeName, "
        "COALESCE(idv.value, '') AS title, i.dateAdded "
        "FROM items i "
        "JOIN itemTypes it ON it.itemTypeID = i.itemTypeID "
        "LEFT JOIN itemData id ON id.itemID = i.itemID "
        "  AND id.fieldID = (SELECT fieldID FROM fields WHERE fieldName='title') "
        "LEFT JOIN itemDataValues idv ON idv.valueID = id.valueID "
        f"WHERE it.typeName NOT IN ('attachment','note','annotation') {where} "
        f"ORDER BY i.dateAdded DESC {tail}"
    ), args


def print_items(db, rows, with_paths=False):
    if not rows:
        print("(没有找到条目)")
        return
    for idx, (item_id, itype, title, _added) in enumerate(rows, 1):
        creators = item_creators(db, item_id)
        year = (item_field(db, item_id, "date") or "")[:4]
        who = " / ".join(creators)
        line = f"[{idx}] {title or '(无标题)'}" + (f" —— {who}" if who else "")
        if year:
            line += f" ({year})"
        line += f"  [{itype}]"
        print(line)
        if with_paths:
            for p in attachment_paths(db, item_id):
                print(f"     📄 {p}")


def main():
    args = sys.argv[1:]
    db = None
    snap = None
    try:
        snap = snapshot_db()
        db = sqlite3.connect(snap)

        if "--collections" in args:
            rows = q(
                db,
                "SELECT c.collectionName, COUNT(ci.itemID) FROM collections c "
                "LEFT JOIN collectionItems ci ON ci.collectionID = c.collectionID "
                "GROUP BY c.collectionID ORDER BY c.collectionName",
            )
            print(f"共 {len(rows)} 个分类：\n")
            for name, count in rows:
                print(f"  {name}  ({count} 条)")
            return

        if "-c" in args:
            i = args.index("-c")
            name = args[i + 1]
            rows = q(
                db,
                "SELECT i.itemID FROM items i "
                "JOIN collectionItems ci ON ci.itemID = i.itemID "
                "JOIN collections c ON c.collectionID = ci.collectionID "
                "WHERE c.collectionName = ? ORDER BY i.dateAdded DESC",
                (name,),
            )
            ids = ",".join(str(r[0]) for r in rows)
            if not ids:
                sys.exit(f"❌ 分类「{name}」不存在或为空（用 --collections 查看全部分类）")
            sql, a = base_query(f"AND i.itemID IN ({ids})")
            print_items(db, q(db, sql, a), with_paths=True)
            return

        if "-s" in args:
            i = args.index("-s")
            keyword = args[i + 1]
            like = f"%{keyword}%"
            sql, a = base_query(
                where=(
                    "AND (idv.value LIKE ? OR i.itemID IN "
                    "  (SELECT ic.itemID FROM itemCreators ic "
                    "   JOIN creators c ON c.creatorID = ic.creatorID "
                    "   WHERE c.firstName LIKE ? OR c.lastName LIKE ?))"
                ),
                args=(like, like, like),
            )
            print_items(db, q(db, sql, a), with_paths=True)
            return

        limit = int(args[0]) if args and args[0].isdigit() else 20
        total = q(db, "SELECT COUNT(*) FROM items i JOIN itemTypes it "
                      "ON it.itemTypeID = i.itemTypeID "
                      "WHERE it.typeName NOT IN ('attachment','note','annotation')")[0][0]
        sql, a = base_query(tail="LIMIT ?")
        print(f"Zotero 库共 {total} 个条目，最近 {min(limit, total)} 个：\n")
        print_items(db, q(db, sql, (limit,)))
        print("\n搜索：python3 scripts/zotero_lib.py -s 关键词 | 分类：--collections")
    finally:
        if db:
            db.close()
        if snap:
            cleanup_snapshot(snap)


if __name__ == "__main__":
    main()
