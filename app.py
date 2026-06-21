#!/usr/bin/env python3
"""
app.py — Serenity Daily 手机端一键推送服务
部署到 Render 免费云服务，手机浏览器打开即可触发推送
"""

import os
import sys
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from io import StringIO
from html.parser import HTMLParser

import requests
from flask import Flask, render_template_string

# ============ 配置 ============
DINGTALK_WEBHOOK = os.environ.get(
    "DINGTALK_WEBHOOK",
    "https://oapi.dingtalk.com/robot/send?access_token=271e4d2114e8303b47517a8017f4a4584af66f1c9a999b06a646afd94a6b2c3d"
)
RSS_URL = "https://rss.app/feeds/cF5wm78REpjmkRdm.xml"
USERNAME = "aleabitoreddit"
# =============================

app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Serenity 推送</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, 'PingFang SC', Helvetica, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .card {
            background: white;
            border-radius: 16px;
            padding: 40px 32px;
            max-width: 400px;
            width: 100%;
            text-align: center;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        }
        .icon { font-size: 48px; margin-bottom: 16px; }
        h1 { font-size: 22px; color: #333; margin-bottom: 8px; }
        p { color: #888; font-size: 14px; margin-bottom: 28px; line-height: 1.5; }
        .btn {
            display: block;
            width: 100%;
            padding: 16px 0;
            font-size: 18px;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
            background: #007AFF;
            color: white;
        }
        .btn:active { transform: scale(0.97); opacity: 0.8; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .status {
            margin-top: 20px;
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
            display: none;
        }
        .status.loading {
            display: block;
            background: #f0f7ff;
            color: #007AFF;
        }
        .status.success {
            display: block;
            background: #e8f8e8;
            color: #28a745;
        }
        .status.error {
            display: block;
            background: #fff0f0;
            color: #dc3545;
        }
        .time { margin-top: 24px; font-size: 12px; color: #bbb; }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">📡</div>
        <h1>Serenity 日报推送</h1>
        <p>点击下方按钮，立即抓取最新帖子并推送到钉钉群</p>
        <form action="/push" method="post">
            <button class="btn" id="pushBtn" type="submit">🚀 立即推送</button>
        </form>
        <div class="status" id="status">{% if message %}{{ message }}{% endif %}</div>
        <div class="time">{{ time }}</div>
    </div>
    <script>
        document.getElementById('pushBtn')?.addEventListener('click', function(e) {
            e.preventDefault();
            var btn = this;
            var status = document.getElementById('status');
            btn.disabled = true;
            btn.textContent = '⏳ 推送中...';
            status.className = 'status loading';
            status.textContent = '正在抓取帖子并推送...';

            fetch('/push', { method: 'POST' })
                .then(function(r) { return r.json(); })
                .then(function(d) {
                    if (d.ok) {
                        status.className = 'status success';
                        status.textContent = '✅ ' + d.message;
                    } else {
                        status.className = 'status error';
                        status.textContent = '❌ ' + d.message;
                    }
                    btn.disabled = false;
                    btn.textContent = '🚀 再次推送';
                })
                .catch(function() {
                    status.className = 'status error';
                    status.textContent = '❌ 请求失败，请重试';
                    btn.disabled = false;
                    btn.textContent = '🚀 立即推送';
                });
        });
    </script>
</body>
</html>
"""


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()


def strip_html(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def fetch_rss(url):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return None


def parse_rss(xml):
    tweets = []
    root = ET.fromstring(xml)
    for item in root.iter("item"):
        try:
            title = item.findtext("title", "")
            desc = item.findtext("description", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            text = desc or title
            text = re.sub(r"<[^>]+>", "", text).strip()
            tweets.append({"text": text, "url": link.strip(), "date": pub_date})
        except:
            continue
    if not tweets:
        for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
            try:
                title = entry.findtext("{http://www.w3.org/2005/Atom}title", "")
                content = entry.findtext("{http://www.w3.org/2005/Atom}content", "")
                link_el = entry.find("{http://www.w3.org/2005/Atom}link")
                link = link_el.get("href", "") if link_el is not None else ""
                published = entry.findtext("{http://www.w3.org/2005/Atom}published", "")
                text = re.sub(r"<[^>]+>", "", content or title).strip()
                tweets.append({"text": text, "url": link.strip(), "date": published})
            except:
                continue
    return tweets


def filter_recent(tweets, hours=24):
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - hours * 3600
    filtered = []
    for t in tweets:
        date_str = t.get("date", "")
        try:
            dt = parsedate_to_datetime(date_str)
            if dt.timestamp() >= cutoff:
                filtered.append(t)
        except:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if dt.timestamp() >= cutoff:
                    filtered.append(t)
            except:
                filtered.append(t)
    return filtered if filtered else tweets


def format_report(tweets):
    if not tweets:
        return f"📡 {USERNAME} 暂无新帖子"
    lines = [
        f"# 📡 {USERNAME} 最新帖子",
        f"> 共 {len(tweets)} 条",
        "---",
    ]
    for i, t in enumerate(tweets, 1):
        text = t.get("text", "")
        url = t.get("url", "")
        date = t.get("date", "")
        lines.append(f"### {i}. {text[:200]}")
        if date:
            lines.append(f"📅 {date}")
        if url:
            lines.append(f"🔗 {url}")
        lines.append("")
    return "\n".join(lines)


def push_to_dingtalk(report):
    keyword = "Serenity"
    if keyword not in report:
        report = f"{keyword}\n\n{report}"
    if len(report.encode("utf-8")) > 18000:
        report = report[:15000] + "\n\n...（内容过长已截断）"
    payload = {
        "msgtype": "markdown",
        "markdown": {"title": f"{USERNAME} 帖子推送", "text": report},
    }
    try:
        resp = requests.post(DINGTALK_WEBHOOK, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
        result = resp.json()
        return result.get("errcode") == 0, result
    except Exception as e:
        return False, str(e)


@app.route("/")
def index():
    from datetime import datetime as dt
    now = dt.now().strftime("%Y-%m-%d %H:%M")
    return render_template_string(HTML_TEMPLATE, time=f"北京时间 {now}", message="")


@app.route("/push", methods=["POST"])
def push():
    try:
        xml = fetch_rss(RSS_URL)
        if not xml:
            return {"ok": False, "message": "RSS 抓取失败"}
        all_tweets = parse_rss(xml)
        recent = filter_recent(all_tweets, hours=24)
        report = format_report(recent)
        ok, detail = push_to_dingtalk(report)
        if ok:
            return {"ok": True, "message": f"推送成功！共 {len(recent)} 条帖子"}
        else:
            return {"ok": False, "message": f"钉钉推送失败: {detail}"}
    except Exception as e:
        return {"ok": False, "message": f"错误: {str(e)}"}
