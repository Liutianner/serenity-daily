#!/usr/bin/env python3
"""
send_dingtalk.py — 命令行即时推送消息到钉钉群

用法:
  export DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=xxx"
  python send_dingtalk.py "你好，这是一条测试消息"
  echo "管道输入也可以" | python send_dingtalk.py
"""

import os
import sys
import requests

DINGTALK_URL = "https://oapi.dingtalk.com/robot/send"


def send_text(webhook_url: str, content: str) -> bool:
    payload = {
        "msgtype": "text",
        "text": {
            "content": content,
        },
    }
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(webhook_url, json=payload, headers=headers, timeout=15)
        result = resp.json()
        if result.get("errcode") == 0:
            print("✅ 推送成功")
            return True
        else:
            print(f"❌ 推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def send_markdown(webhook_url: str, title: str, content: str) -> bool:
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
            print("✅ 推送成功")
            return True
        else:
            print(f"❌ 推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def main():
    webhook = os.environ.get("DINGTALK_WEBHOOK", "")
    if not webhook:
        print("❌ 请先设置环境变量 DINGTALK_WEBHOOK")
        print("   export DINGTALK_WEBHOOK=\"https://oapi.dingtalk.com/robot/send?access_token=xxx\"")
        sys.exit(1)

    # 获取消息内容：优先命令行参数，其次管道输入
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        message = sys.stdin.read().strip()
    else:
        print("❌ 请提供要发送的消息")
        print("   用法: python send_dingtalk.py \"你的消息\"")
        sys.exit(1)

    if not message:
        print("❌ 消息内容不能为空")
        sys.exit(1)

    # 判断是否 markdown（含 markdown 标记则用 markdown 格式发送）
    md_chars = {"#", "*", "`", "[", "]", "- ", "1."}
    is_md = any(marker in message for marker in md_chars)

    if is_md:
        title = message.split("\n")[0][:50]
        send_markdown(webhook, title, message)
    else:
        send_text(webhook, message)


if __name__ == "__main__":
    main()
