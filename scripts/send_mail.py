#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过 QQ 邮箱发送邮件（SMTP 方式）

用途：
    以 627157471@qq.com（显示名 Wonder）的名义发送一封文本邮件。

用法：
    python3 scripts/send_mail.py <收件人邮箱> "<主题>" "<正文>"

    例：
    python3 scripts/send_mail.py 1234567@qq.com "会议通知" "周五上午10点开会"

    正文较长时，用 - 表示从标准输入读取：
    cat 正文.txt | python3 scripts/send_mail.py 1234567@qq.com "主题" -

说明：
    授权码从 macOS 钥匙串读取（服务名 qq-mail），本文件不保存任何密钥。
    QQ 邮箱规定：发件人必须与登录账号一致，所以本脚本只能用 627157471@qq.com 发信。
"""

import smtplib
import subprocess
import sys
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
EMAIL_ADDR = "627157471@qq.com"
DISPLAY_NAME = "Wonder"
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


def main():
    if len(sys.argv) < 3:
        sys.exit("用法：python3 scripts/send_mail.py <收件人邮箱> <主题> [正文|-]")

    to_addr = sys.argv[1]
    subject = sys.argv[2]
    body_arg = sys.argv[3] if len(sys.argv) > 3 else ""

    if body_arg == "-":
        body = sys.stdin.read()
    elif body_arg:
        body = body_arg
    else:
        print("请输入正文（结束后按 Ctrl+D 提交）：")
        body = sys.stdin.read()

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((Header(DISPLAY_NAME, "utf-8").encode(), EMAIL_ADDR))
    msg["To"] = to_addr
    msg["Date"] = formatdate(localtime=True)

    try:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        server.login(EMAIL_ADDR, get_auth_code())
        server.sendmail(EMAIL_ADDR, [to_addr], msg.as_string())
        server.quit()
        print(f"✅ 邮件已发送给 {to_addr}")
    except smtplib.SMTPAuthenticationError:
        sys.exit("❌ 登录失败：授权码不正确，或 QQ 邮箱未开启 IMAP/SMTP 服务")
    except Exception as e:
        sys.exit(f"❌ 发送失败：{e}")


if __name__ == "__main__":
    main()
