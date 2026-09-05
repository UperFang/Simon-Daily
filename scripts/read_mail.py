#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取 QQ 邮箱的最新邮件（IMAP 方式）

用途：
    列出收件箱最新 N 封邮件的日期、发件人、主题；
    加 --body 序号 可查看列表中某一封的正文。

用法：
    python3 scripts/read_mail.py             # 列出最新 10 封
    python3 scripts/read_mail.py 20          # 列出最新 20 封
    python3 scripts/read_mail.py --body 1    # 查看最新第 1 封的正文

说明：
    授权码从 macOS 钥匙串读取（服务名 qq-mail），本文件不保存任何密钥。
    运行环境需要能联网；QQ 邮箱需已开启 IMAP/SMTP 服务。
"""

import imaplib
import subprocess
import re
import sys
from email.header import decode_header

IMAP_HOST = "imap.qq.com"
EMAIL_ADDR = "627157471@qq.com"
KEYCHAIN_SERVICE = "qq-mail"


def get_auth_code():
    """从 macOS 钥匙串读取授权码"""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(
            "❌ 无法从钥匙串读取授权码，请先执行：\n"
            f'  security add-generic-password -a "{EMAIL_ADDR}" '
            f'-s "{KEYCHAIN_SERVICE}" -w "16位授权码"'
        )
    return result.stdout.strip()


def decode_str(s):
    """解码邮件头（发件人、主题）中的中文等编码内容"""
    if not s:
        return ""
    parts = []
    for data, charset in decode_header(s):
        if isinstance(data, bytes):
            parts.append(data.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(data)
    return "".join(parts)


def get_body(msg):
    """提取邮件正文：优先纯文本，退而求其次解析 HTML"""
    if msg.is_multipart():
        for ctype in ("text/plain", "text/html"):
            for part in msg.walk():
                if part.get_content_type() == ctype:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    text = payload.decode(charset, errors="replace")
                    if ctype == "text/html":
                        text = re.sub(r"<[^>]+>", " ", text)
                        text = re.sub(r"\s+", " ", text)
                    return text.strip()
        return "(无法解析正文)"
    payload = msg.get_payload(decode=True)
    if payload is None:
        return str(msg.get_payload())
    charset = msg.get_content_charset() or "utf-8"
    text = payload.decode(charset, errors="replace")
    if msg.get_content_type() == "text/html":
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
    return text.strip()


def main():
    args = sys.argv[1:]
    show_body_idx = None   # 列表中的序号（1 = 最新一封）
    limit = 10
    if "--body" in args:
        i = args.index("--body")
        if i + 1 >= len(args):
            sys.exit("用法：python3 scripts/read_mail.py --body <序号>")
        show_body_idx = int(args[i + 1])
    elif args:
        limit = int(args[0])

    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(EMAIL_ADDR, get_auth_code())
    try:
        mail.select("INBOX")
        status, data = mail.search(None, "ALL")
        if status != "OK":
            sys.exit("❌ 搜索邮件失败")
        ids = data[0].split()
        total = len(ids)
        if total == 0:
            print("收件箱是空的")
            return

        if show_body_idx is not None:
            if not 1 <= show_body_idx <= min(limit, total):
                sys.exit(f"❌ 序号超出范围（1 ~ {min(limit, total)}）")
            msg = mail.fetch(ids[total - show_body_idx], "(RFC822)")[1][0][1]
            msg = email_message_from_bytes(msg)
            print(f"发件人：{decode_str(msg.get('From'))}")
            print(f"主  题：{decode_str(msg.get('Subject'))}")
            print(f"日  期：{decode_str(msg.get('Date'))}")
            print("-" * 40)
            print(get_body(msg))
        else:
            n = min(limit, total)
            print(f"收件箱共 {total} 封，最新 {n} 封：\n")
            for rank in range(1, n + 1):
                msg = mail.fetch(ids[total - rank], "(RFC822)")[1][0][1]
                msg = email_message_from_bytes(msg)
                print(f"[{rank}] {decode_str(msg.get('Date'))}")
                print(f"    来自：{decode_str(msg.get('From'))}")
                print(f"    主题：{decode_str(msg.get('Subject'))}")
            print("\n查看正文：python3 scripts/read_mail.py --body <序号>")
    finally:
        mail.logout()


def email_message_from_bytes(raw):
    """把原始字节转成 email 对象（单独包一层便于阅读）"""
    import email
    return email.message_from_bytes(raw)


if __name__ == "__main__":
    main()
