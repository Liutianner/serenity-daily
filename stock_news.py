#!/usr/bin/env python3
"""
stock_news.py — 每日股票新闻推送
从新浪财经获取多个频道新闻，汇总推送至钉钉群

API: feed.mix.sina.com.cn/api/roll/get
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

import requests

# 钉钉推送地址
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "") or \
    "https://oapi.dingtalk.com/robot/send?access_token=271e4d2114e8303b47517a8017f4a4584af66f1c9a999b06a646afd94a6b2c3d"

# 新闻源配置
CHANNELS = {
    2509: "美股",
    2518: "港股",
    2519: "基金",
    2544: "科技",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch_channel(lid: int, count: int = 8) -> list:
    """获取单个频道的新闻"""
    url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid={lid}&knum={count}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("result", {}).get("data", [])
        return [
            {
                "title": item.get("title", ""),
                "intro": item.get("intro", ""),
                "url": item.get("url", ""),
                "channel": CHANNELS.get(lid, ""),
                "media": item.get("media_name", ""),
            }
            for item in items
            if item.get("title")
        ]
    except Exception as e:
        print(f"  ⚠️ 频道 {CHANNELS.get(lid, lid)} 请求失败: {e}")
        return []


def build_report(all_news: list) -> str:
    """生成 Markdown 报告"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append("# 📈 每日财经新闻速递")
    lines.append(f"> 更新时间: {now}")
    lines.append(f"> 来源: 新浪财经")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not all_news:
        lines.append("*暂无新闻。*")
        return "\n".join(lines)

    # 按频道分组
    grouped = {}
    for n in all_news:
        ch = n["channel"]
        if ch not in grouped:
            grouped[ch] = []
        grouped[ch].append(n)

    for ch_name in ["美股", "港股", "科技", "基金"]:
        items = grouped.get(ch_name, [])
        if not items:
            continue
        lines.append(f"## 🌍 {ch_name}")
        lines.append("")
        for i, item in enumerate(items, 1):
            title = item["title"]
            intro = item["intro"]
            url = item["url"]
            media = item["media"]

            lines.append(f"### {i}. {title}")
            if intro:
                # 截断过长简介
                brief = intro[:150] + ("..." if len(intro) > 150 else "")
                lines.append(f">{brief}")
                lines.append("")
            if media:
                lines.append(f"📰 {media}")
            if url:
                lines.append(f"🔗 [阅读原文]({url})")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("*本日报由 Serenity Daily 自动生成*")
    return "\n".join(lines)


def push_to_dingtalk(report: str) -> bool:
    """推送报告到钉钉群"""
    keyword = "Serenity"
    if keyword not in report:
        report = f"{keyword}\n\n{report}"

    if len(report.encode("utf-8")) > 18000:
        report = report[:15000] + "\n\n...（内容过长已截断）"

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "每日财经新闻速递",
            "text": report,
        },
    }
    try:
        resp = requests.post(DINGTALK_WEBHOOK, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
        result = resp.json()
        if result.get("errcode") == 0:
            print("✅ 钉钉推送成功")
            return True
        else:
            print(f"❌ 钉钉推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def main():
    print("=" * 50)
    print("📈 获取财经新闻")
    print(f"   时间: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    all_news = []
    seen_titles = set()

    for lid in CHANNELS:
        print(f"  抓取 {CHANNELS[lid]}...")
        items = fetch_channel(lid)
        for item in items:
            if item["title"] not in seen_titles:
                seen_titles.add(item["title"])
                all_news.append(item)

    print(f"\n📊 共获取 {len(all_news)} 条新闻 (去重后)")

    report = build_report(all_news)

    # 保存到文件（调试用）
    with open("stock_news_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("📄 报告已保存: stock_news_report.md")

    success = push_to_dingtalk(report)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
