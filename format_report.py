#!/usr/bin/env python3
"""
format_report.py — 将抓取的帖子整理为结构化报告
"""

import json
import os
from datetime import datetime

INPUT_FILE = "raw_posts.json"
OUTPUT_FILE = "report.md"


def load_posts(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_report(data: dict) -> str:
    tweets = data.get("tweets", [])
    username = data.get("username", "serenity")
    fetched_at = data.get("fetched_at", "")
    today_count = data.get("recent_count", data.get("today_count", 0))
    total_count = data.get("total_count", 0)

    # 尝试解析抓取时间
    try:
        dt = datetime.fromisoformat(fetched_at)
        date_str = dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        date_str = fetched_at

    lines = []
    lines.append(f"# 📡 Serenity (@{username}) 今日帖子摘要")
    lines.append(f"")
    lines.append(f"> 抓取时间: {date_str}")
    lines.append(f"> 当日帖子: {today_count} | 总帖子数: {total_count}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    if not tweets:
        lines.append("*今日无新帖子。*")
        return "\n".join(lines)

    for i, t in enumerate(tweets, 1):
        text = t.get("text", "")
        url = t.get("url", "")
        date = t.get("date", "")

        # 截取前 120 字作为预览
        preview = text[:120] + ("..." if len(text) > 120 else "")

        lines.append(f"### {i}. {preview}")
        lines.append(f"")
        lines.append(f"{text}")
        lines.append(f"")
        if date:
            lines.append(f"📅 {date}")
        if url:
            lines.append(f"🔗 [查看原文]({url})")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    # 尾部统计
    lines.append(f"*共 {len(tweets)} 条帖子 — Serenity 日报由自动化工具自动生成*")

    return "\n".join(lines)


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 找不到 {INPUT_FILE}，请先运行 fetch_posts.py")
        return

    data = load_posts(INPUT_FILE)
    report = build_report(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"📄 报告已生成: {OUTPUT_FILE}")
    print(f"   共 {data.get('today_count', 0)} 条帖子")


if __name__ == "__main__":
    main()
