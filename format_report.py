#!/usr/bin/env python3
"""
format_report.py — Format scraped posts into a structured English Markdown report
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
    recent_count = data.get("recent_count", data.get("today_count", 0))
    total_count = data.get("total_count", 0)

    try:
        dt = datetime.fromisoformat(fetched_at)
        date_str = dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        date_str = fetched_at

    lines = []
    lines.append(f"# 📡 Serenity (@{username}) Daily Digest")
    lines.append(f"")
    lines.append(f"> Fetched: {date_str}")
    lines.append(f"> Recent posts: {recent_count} | Total: {total_count}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    if not tweets:
        lines.append("*No new posts.*")
        return "\n".join(lines)

    for i, t in enumerate(tweets, 1):
        text = t.get("text", "")
        url = t.get("url", "")
        date = t.get("date", "")

        preview = text[:120] + ("..." if len(text) > 120 else "")

        lines.append(f"### {i}. {preview}")
        lines.append(f"")
        lines.append(f"{text}")
        lines.append(f"")
        if date:
            lines.append(f"📅 {date}")
        if url:
            lines.append(f"🔗 [Source]({url})")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    lines.append(f"*{len(tweets)} posts — Automated Serenity Daily Digest*")

    return "\n".join(lines)


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Cannot find {INPUT_FILE}, run fetch_posts.py first")
        return

    data = load_posts(INPUT_FILE)
    report = build_report(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"📄 Report generated: {OUTPUT_FILE}")
    print(f"   {data.get('recent_count', 0)} posts")


if __name__ == "__main__":
    main()
