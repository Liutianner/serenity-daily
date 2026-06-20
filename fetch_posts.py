#!/usr/bin/env python3
"""
fetch_posts.py — 从 Nitter 实例抓取 X/Twitter 用户 @serenity 的帖子
"""

import json
import sys
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

# Nitter 镜像列表
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
    "https://nitter.poast.org",
    "https://nitter.cz",
    "https://nitter.lacontrevoie.fr",
    "https://nitter.nl",
]

USERNAME = "serenity"
OUTPUT_FILE = "raw_posts.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def fetch_html(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"    ⚠️  {e}")
        return None


def parse_tweets(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    tweets = []

    for item in soup.select("div.timeline-item"):
        try:
            content_el = item.select_one("div.tweet-content")
            if not content_el:
                continue
            text = content_el.get_text(strip=True)
            if not text:
                continue

            # 日期
            time_el = item.select_one("span.tweet-date time")
            pub_date = time_el.get("datetime", "") if time_el else ""

            # 链接
            link_el = item.select_one("a.tweet-link")
            url = ""
            if link_el:
                href = link_el.get("href", "")
                url = f"https://nitter.net{href}" if href.startswith("/") else href

            tweets.append({
                "text": text,
                "url": url,
                "date": pub_date,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            print(f"    ⚠️  解析出错: {e}")
            continue

    return tweets


def main():
    print("=" * 50)
    print(f"📡 抓取 @{USERNAME} 的帖子")
    print(f"   时间: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    all_tweets = []
    instance_used = ""

    for inst in NITTER_INSTANCES:
        url = f"{inst}/{USERNAME}"
        print(f"\n🌐 尝试: {url}")
        html = fetch_html(url)
        if not html:
            print(f"    ❌ 不可用")
            continue
        tweets = parse_tweets(html)
        if tweets:
            all_tweets = tweets
            instance_used = inst
            print(f"    ✅ 成功解析 {len(tweets)} 条帖子")
            break
        else:
            print(f"    ⚠️ 无内容")
            continue

    if not all_tweets:
        print("\n❌ 所有 Nitter 实例均不可用")
        sys.exit(1)

    # 尝试按今天筛选
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_posts = [t for t in all_tweets if today_str in t.get("date", "")]
    final_posts = today_posts if today_posts else all_tweets

    print(f"\n📊 当日帖子: {len(today_posts)} / 总计: {len(all_tweets)}")

    output = {
        "username": USERNAME,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "instance_used": instance_used,
        "today_count": len(today_posts),
        "total_count": len(all_tweets),
        "is_today_only": bool(today_posts),
        "tweets": final_posts,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"💾 -> {OUTPUT_FILE}")
    print("✅ 完成")


if __name__ == "__main__":
    main()
