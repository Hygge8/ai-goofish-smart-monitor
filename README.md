# 闲鱼摩托车监控助手

一个面向“闲鱼 / goofish 摩托车商品”的监控项目，支持关键词监控、价格过滤、AI/规则推荐、SQLite 去重、钉钉机器人图文卡片通知。

重点解决你之前遇到的问题：

- 通知不能只发一长串链接；
- 商品图片要显示在钉钉消息里；
- 电脑端链接和手机端链接不要堆在正文里；
- 只保留按钮入口，例如“立即查看”“发起聊天”；
- `{{content}}` 不再拼接长链接，避免消息刷屏。

## 效果

钉钉通知使用 `actionCard` 图文卡片：

```text
商品图片

闲鱼摩托车监控：🚨 新推荐！
类型：新发布  关键词：摩托车
价格：￥5000  地区：广东
标题：自用23年准信5000公里实表赛科龙ra2
推荐理由：价格低于市场均价，个人卖家，描述清晰。
商家：广东个人玩家

[发起聊天] [立即查看]
```

## 目录结构

```text
goofish-moto-monitor
├── config.example.yaml          # 配置模板
├── docker-compose.yml           # Docker 编排
├── Dockerfile
├── requirements.txt
├── src/goofish_monitor/
│   ├── cli.py                   # 命令行入口
│   ├── config.py                # 配置加载
│   ├── db.py                    # SQLite 去重
│   ├── monitor.py               # 主监控循环
│   ├── scraper.py               # Playwright 商品采集
│   ├── ai.py                    # AI/规则推荐
│   ├── url_utils.py             # 链接规整，避免长链接
│   ├── web.py                   # 简单 Web 状态页
│   └── notifier/dingtalk.py     # 钉钉图文卡片通知
└── scripts/setup_playwright.sh
```

## 快速启动

### 1. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

### 2. 准备配置

```bash
cp config.example.yaml config.yaml
cp .env.example .env
```

编辑 `.env`：

```env
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxxx
DINGTALK_SECRET=SECxxxx
```

编辑 `config.yaml`，例如：

```yaml
monitor:
  interval_seconds: 60
  headless: true
  max_items_per_keyword: 20

tasks:
  - name: 摩托车
    keyword: 摩托车
    min_price: 1000
    max_price: 20000
    include_words: ["准新", "个人", "自用", "无事故"]
    exclude_words: ["事故", "水泡", "抵押", "报废"]
```

### 3. 运行一次测试通知

```bash
python -m goofish_monitor.cli test-dingtalk --config config.yaml
```

### 4. 开始监控

```bash
python -m goofish_monitor.cli run --config config.yaml
```

### 5. Web 状态页

```bash
uvicorn goofish_monitor.web:app --host 0.0.0.0 --port 8080
```

访问：

```text
http://服务器IP:8080
```

## Docker 部署

```bash
docker compose up -d --build
```

查看日志：

```bash
docker compose logs -f monitor
```

## 图片显示说明

钉钉卡片里的图片必须是公网可访问的 HTTPS 图片地址。

本项目优先使用闲鱼页面里抓到的商品首图 `image_url`。如果你后面把图片下载到本地，钉钉无法直接显示本地路径，需要再配置 OSS、图床或自己的静态文件服务器。

## 钉钉通知为什么不用 markdown？

普通 `markdown` 消息容易出现这种问题：

```text
手机端链接：https://pages.goofish.com/sharexy?loadingVisible=false&...
电脑端链接：https://www.goofish.com/item?id=...
```

链接很长，会把群消息刷屏。

所以这里改成 `actionCard`：正文只展示商品信息，链接全部放到按钮里。

## 注意

闲鱼页面结构可能变化，`scraper.py` 里做了多种兜底解析，但如果页面改版，可能需要调整选择器。

建议先本地运行：

```bash
python -m goofish_monitor.cli search --keyword 摩托车 --limit 5
```

确认能抓到标题、价格、图片、链接后，再开启钉钉推送。
