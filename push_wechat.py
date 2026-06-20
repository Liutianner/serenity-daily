#!/usr/bin/env python3
"""
push_wechat.py — 通过 PushPlus 推送到微信
"""

import json
import os
import sys

import requests

INPUT_FILE = "report.md"
PUSHPLUS_URL = "https://www.pushplus.plus/send"


def load_report(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def send_to_wechat(token: str, title: str, content: str) -> bool:
    payload = {
        "token": token,
        "title": title,
        "content": content,
        "template": "markdown",
        "channel": "wechat",
    }
    try:
        resp = requests.post(PUSHPLUS_URL, json=payload, timeout=15)
        result = resp.json()
        if result.get("code") == 200:
            print("✅ PushPlus 推送成功")
            return True
        else:
            print(f"❌ PushPlus 推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ PushPlus 请求异常: {e}")
        return False


def main():
    token = os.environ.get("PUSHPLUS_TOKEN", "")
    if not token:
        print("❌ 未设置环境变量 PUSHPLUS_TOKEN")
        sys.exit(1)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ 找不到 {INPUT_FILE}，请先运行 format_report.py")
        sys.exit(1)

    report = load_report(INPUT_FILE)
    title = "📡 Serenity 今日帖子摘要"

    # 限制 content 长度（PushPlus 建议不超过 10 万字，这里大部分情况没问题）
    if len(report) > 80000:
        report = report[:80000] + "\n\n...（内容过长已截断）"

    success = send_to_wechat(token, title, report)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
