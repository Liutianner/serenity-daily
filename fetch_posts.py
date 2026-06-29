#!/usr/bin/env python3
"""
fetch_posts.py — 从 RSS Feed 抓取 X/Twitter 帖子
"""

import json
import sys
from datetime import datetime, timezone
from typing import Optional

import requests

# Nitter RSS 源（替代 rss.app，因免费额度用完）
RSS_URL = "https://nitter.net/aleabitoreddit/rss"
OUTPUT_FILE = "raw_posts.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/xml,application/xml,application/xhtml+xml",
}


def fetch_rss(url: str) -> Optional[str]:
    """抓取 RSS XML"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  ❌ RSS 请求失败: {e}")
        return None


def parse_rss(xml: str) -> list:
    """解析 RSS XML，提取帖子"""
    import xml.etree.ElementTree as ET

    tweets = []
    root = ET.fromstring(xml)

    # RSS namespace
    ns = {"": "http://www.w3.org/2005/Atom"}

    # 尝试标准 RSS 2.0 格式
    for item in root.iter("item"):
        try:
            title = item.findtext("title", "")
            desc = item.findtext("description", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")

            # 优先用 description（通常包含推文正文）
            text = desc or title

            # 清理 HTML 标签
            import re
            text = re.sub(r"<[^>]+>", "", text).strip()

            tweets.append({
                "text": text,
                "url": link.strip(),
                "date": pub_date,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            print(f"  ⚠️ 解析条目出错: {e}")
            continue

    # 如果 RSS 2.0 没找到，试试 Atom 格式
    if not tweets:
        for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
            try:
                title = entry.findtext("{http://www.w3.org/2005/Atom}title", "")
                content = entry.findtext("{http://www.w3.org/2005/Atom}content", "")
                link_el = entry.find("{http://www.w3.org/2005/Atom}link")
                link = link_el.get("href", "") if link_el is not None else ""
                published = entry.findtext("{http://www.w3.org/2005/Atom}published", "")

                import re
                text = re.sub(r"<[^>]+>", "", content or title).strip()

                tweets.append({
                    "text": text,
                    "url": link.strip(),
                    "date": published,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as e:
                print(f"  ⚠️ 解析 Atom 条目出错: {e}")
                continue

    return tweets


def filter_recent(tweets: list, hours: int = 48) -> list:
    """筛选最近 N 小时的帖子"""
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - hours * 3600
    filtered = []

    # 常见时间格式
    from email.utils import parsedate_to_datetime

    for t in tweets:
        date_str = t.get("date", "")
        try:
            # 尝试 RFC 2822 (RSS 标准)
            dt = parsedate_to_datetime(date_str)
            if dt.timestamp() >= cutoff:
                filtered.append(t)
        except Exception:
            try:
                # 尝试 ISO 格式 (Atom)
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if dt.timestamp() >= cutoff:
                    filtered.append(t)
            except Exception:
                # 未知格式，保留全部
                filtered.append(t)
                continue

    return filtered if filtered else tweets


def main():
    print("=" * 50)
    print("📡 通过 RSS 抓取 @aleabitoreddit 的帖子")
    print(f"   时间: {datetime.now(timezone.utc).isoformat()}")
    print(f"   RSS: {RSS_URL}")
    print("=" * 50)

    xml = fetch_rss(RSS_URL)
    if not xml:
        sys.exit(1)

    all_tweets = parse_rss(xml)
    print(f"\n📊 RSS 解析到 {len(all_tweets)} 条帖子")

    recent = filter_recent(all_tweets, hours=24)
    print(f"   近 48 小时: {len(recent)} 条")

    output = {
        "username": "aleabitoreddit",
        "source": "RSS",
        "rss_url": RSS_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(all_tweets),
        "recent_count": len(recent),
        "tweets": recent,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"💾 -> {OUTPUT_FILE}")
    print("✅ 完成")


if __name__ == "__main__":
    main()
