#!/usr/bin/env python3
"""
push_dingtalk.py — 通过钉钉自定义机器人推送报告
"""

import json
import os
import sys

import requests

INPUT_FILE = "report.md"
DINGTALK_URL = "https://oapi.dingtalk.com/robot/send"


def load_report(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def convert_markdown_for_dingtalk(content: str) -> str:
    """
    钉钉 markdown 有一些限制，做一些兼容处理：
      - 不支持 [toc]
      - 不支持某些 HTML
      - 链接渲染可能有差异，但基本 markdown 都支持
    这里只做基本清理
    """
    # 移除不兼容的语法
    lines = content.split("\n")
    cleaned = [line for line in lines if not line.strip().startswith("[toc]")]
    return "\n".join(cleaned)


def send_to_dingtalk(webhook_url: str, title: str, content: str) -> bool:
    # 钉钉消息体大小限制约 20KB，超长会被截断或拒绝
    if len(content.encode("utf-8")) > 18000:
        content = content[:15000] + "\n\n...（内容过长已截断）"

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content,
        },
    }
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(webhook_url, json=payload, headers=headers, timeout=15)
        result = resp.json()
        if result.get("errcode") == 0:
            print("✅ 钉钉推送成功")
            return True
        else:
            print(f"❌ 钉钉推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 钉钉请求异常: {e}")
        return False


def main():
    webhook_url = os.environ.get("DINGTALK_WEBHOOK", "")
    if not webhook_url:
        print("❌ 未设置环境变量 DINGTALK_WEBHOOK")
        print("   在 GitHub Secrets 中添加，值如:")
        print("   https://oapi.dingtalk.com/robot/send?access_token=xxx")
        sys.exit(1)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ 找不到 {INPUT_FILE}，请先运行 format_report.py")
        sys.exit(1)

    report = load_report(INPUT_FILE)
    report = convert_markdown_for_dingtalk(report)
    # 钉钉关键词匹配要求：消息内容必须包含关键词
    keyword = "Serenity"
    if keyword not in report:
        report = f"{keyword}\n\n{report}"
    title = f"{keyword} 今日帖子摘要"

    success = send_to_dingtalk(webhook_url, title, report)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
