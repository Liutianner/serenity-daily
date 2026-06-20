#!/usr/bin/env python3
"""
format_report.py — 将抓取的帖子翻译为中文并生成报告
"""

import json
import os
from datetime import datetime

from deep_translator import GoogleTranslator

INPUT_FILE = "raw_posts.json"
OUTPUT_FILE = "report.md"

# 初始化翻译器（全局复用，避免重复创建）
_translator = None


def get_translator():
    global _translator
    if _translator is None:
        _translator = GoogleTranslator(source="en", target="zh-CN")
    return _translator


def translate_text(text: str, max_len: int = 3000) -> str:
    """将英文翻译为中文，超长文本分段翻译"""
    if not text or len(text.strip()) == 0:
        return text
    try:
        t = get_translator()
        # Google Translate 有字符限制，超长分段处理
        if len(text) > max_len:
            parts = []
            remaining = text
            while remaining:
                part = remaining[:max_len]
                # 尽量在句号处断开
                cut = part.rfind(". ")
                if cut > max_len // 2:
                    part = part[: cut + 1]
                    remaining = remaining[cut + 1 :]
                else:
                    remaining = remaining[max_len:]
                try:
                    parts.append(t.translate(part))
                except Exception:
                    parts.append(part)
            return " ".join(parts)
        else:
            return t.translate(text)
    except Exception as e:
        print(f"  ⚠️ 翻译失败: {e}")
        return text  # 翻译失败则返回原文


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
    lines.append(f"# 📡 Serenity (@{username}) 今日帖子摘要（中文翻译）")
    lines.append(f"")
    lines.append(f"> 抓取时间: {date_str}")
    lines.append(f"> 近期帖子: {recent_count} | 总计: {total_count}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    if not tweets:
        lines.append("*今日暂无新帖子。*")
        return "\n".join(lines)

    for i, t in enumerate(tweets, 1):
        text = t.get("text", "")
        url = t.get("url", "")
        date = t.get("date", "")

        # 翻译正文
        print(f"  翻译第 {i} 条帖子...")
        translated = translate_text(text)

        preview = translated[:120] + ("..." if len(translated) > 120 else "")

        lines.append(f"### {i}. {preview}")
        lines.append(f"")
        lines.append(f"{translated}")
        lines.append(f"")
        lines.append("---")
        lines.append("**原文参考：**")
        lines.append(f"> {text[:300]}{'...' if len(text) > 300 else ''}")
        lines.append(f"")
        if date:
            lines.append(f"📅 {date}")
        if url:
            lines.append(f"🔗 [查看原文]({url})")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    lines.append(f"*共 {len(tweets)} 条帖子 — Serenity 日报自动翻译生成*")

    return "\n".join(lines)


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 找不到 {INPUT_FILE}，请先运行 fetch_posts.py")
        return

    data = load_posts(INPUT_FILE)
    print(f"📖 开始翻译 {data.get('recent_count', 0)} 条帖子...")
    report = build_report(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"📄 报告已生成: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
