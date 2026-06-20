# Serenity Daily Digest 🐦→📱

自动抓取 X/Twitter 用户 **@serenity** 的每日帖子，整理成结构化报告，推送到你的钉钉。

## 架构

```
Nitter (Twitter镜像)  →  GitHub Actions (定时任务)  →  钉钉群机器人
    每天 UTC 00:00 抓取    │                             
                           ├─ fetch_posts.py     ← 抓取帖子
                           ├─ format_report.py   ← 整理为 Markdown
                           └─ push_dingtalk.py   ← 推送到钉钉
```

## 部署步骤（约 10 分钟）

### 0️⃣ 准备工作

- ✅ 一个 **GitHub 账号**（[注册](https://github.com/signup)）
- ✅ 一个 **钉钉群**（自己建一个单人群或随便拉个群）

### 1️⃣ 获取钉钉 Webhook 地址

1. 打开钉钉 → 创建一个群（或进入已有的群）
2. 点击群设置 → **智能群助手** → **添加机器人**
3. 选择 **自定义**（通过 Webhook 接入）
4. 机器人名字随便填（比如 "Serenity 日报"）
5. **安全设置** → 勾选 **加签** → 复制生成的密钥（SEC...开头的一长串）→ 点完成
6. 复制 **Webhook 地址**，看起来像：
   ```
   https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxx
   ```
7. 如果勾选了加签，最终的 URL 需要拼接成：
   ```
   https://oapi.dingtalk.com/robot/send?access_token=你的token&timestamp=xxx&sign=xxx
   ```
   > 但 GitHub Actions 里用加签比较麻烦，建议**先不加签**（选"自定义关键词"），设置关键词 `Serenity` 即可


#### 方式 A：关键词校验（推荐，最简单）

在安全设置勾选 **自定义关键词**，输入 `Serenity`。
这样只要消息内容包含 "Serenity" 就能通过，无需额外配置。

#### 方式 B：加签（更安全，需要改脚本）

如果用加签，需要额外在 `push_dingtalk.py` 里实现签名逻辑。我也可以帮你改。

> **建议先用方式 A**，以后想上生产再加签。| 文件 | 作用 |
|:----|:-----|
| `fetch_posts.py` | 从 Nitter 镜像抓取 @serenity 的帖子 |
| `format_report.py` | 将 JSON 帖子整理为可读的 Markdown 报告 |
| `push_dingtalk.py` | 推送到钉钉群机器人 |
| `.github/workflows/daily.yml` | GitHub Actions 定时任务配置 |
| `requirements.txt` | Python 依赖 |
| `raw_posts.json` | 抓取的原始数据（自动生成） |
| `report.md` | 整理后的报告（自动生成） |

### 2️⃣ 把代码部署到 GitHub

#### 方式一：一键 Fork（推荐）

1. 打开 https://github.com/new 创建一个新仓库，取名 `serenity-daily`
2. 在本项目目录下运行：

```bash
# 克隆你的仓库
git clone https://github.com/<你的用户名>/serenity-daily.git
cd serenity-daily

# 把本项目文件复制进去
cp -r /path/to/serenity-daily/* .

# 提交推送
git add .
git commit -m "init: serenity daily digest"
git push
```

#### 方式二：直接在 GitHub 网页创建

1. 登录 GitHub → 点击绿色 `New` 按钮创建新仓库 `serenity-daily`
2. 进入仓库 → 点击 `Add file` → `Upload files`
3. 将本项目所有文件上传

### 3️⃣ 设置钉钉 Webhook（Secrets）

1. 进入你的 GitHub 仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. **Name**: `DINGTALK_WEBHOOK`
5. **Secret**: 粘贴你的完整钉钉 Webhook 地址
   ```
   https://oapi.dingtalk.com/robot/send?access_token=你的token
   ```
6. 点击 **Add secret**

### 4️⃣ 启用 GitHub Actions

1. 进入仓库 → 点击 **Actions** 标签
2. 如果提示 "Workflows"，点击 **I understand my workflows, go ahead and enable them**
3. 在左侧找到 **Serenity Daily Digest**
4. 点击 **Enable workflow**

### 5️⃣ 手动测试运行

1. 进入 **Actions** → **Serenity Daily Digest**
2. 点击 **Run workflow** → **Run workflow**
3. 等待几秒钟，绿色的 ✓ 表示运行成功
4. **检查你的微信** — 应该已经收到推送了！

### 6️⃣ 自动运行

部署完成后，GitHub Actions 会自动：
- **每天北京时间 08:00** 运行一次
- 抓取 @serenity 前一天的帖子
- 整理成 Markdown 报告
- 推送到你的微信

你也可以随时进入仓库 → Actions → **Run workflow** 手动触发。

## 文件说明

| 文件 | 作用 |
|:----|:-----|
| `fetch_posts.py` | 从 Nitter 镜像抓取 @serenity 的帖子 |
| `format_report.py` | 将 JSON 帖子整理为可读的 Markdown 报告 |
| `push_wechat.py` | 通过 PushPlus API 推送到微信 |
| `.github/workflows/daily.yml` | GitHub Actions 定时任务配置 |
| `requirements.txt` | Python 依赖 |
| `raw_posts.json` | 抓取的原始数据（自动生成） |
| `report.md` | 整理后的报告（自动生成） |

## 自定义

### 修改推送时间

编辑 `.github/workflows/daily.yml`，修改 cron 表达式：

```yaml
on:
  schedule:
    - cron: '0 0 * * *'   # UTC 00:00 = 北京时间 08:00
```

### 添加更多推送渠道

可以修改 `push_wechat.py`，改为飞书、钉钉、Telegram 等。

### 修改追踪用户

编辑 `fetch_posts.py` 第 23 行：

```python
USERNAME = "serenity"  # 改成你要追踪的 Twitter 用户名
```

## 故障排除

| 问题 | 原因 | 解决方法 |
|:----|:-----|:---------|
| 钉钉没收到推送 | Webhook 地址没设对 | 检查 Secrets 中的 `DINGTALK_WEBHOOK` |
| 钉钉报错 "关键词不匹配" | 安全设置选了"关键词"但消息里没有 | 在钉钉机器人安全设置中添加关键词 `Serenity` |
| 抓取到 0 条帖子 | 所有 Nitter 镜像都挂了 | 去 [Nitter 可用实例列表](https://github.com/zedeus/nitter/wiki/Instances) 更新 `fetch_posts.py` |
| GitHub Actions 报错 403 | Nitter 被屏蔽 | 等待下一次运行，或手动触发重试 |
| 报告内容不完整 | 帖子太多被截断 | 正常情况不会发生，除非一天发了几百条 |

## License

MIT
