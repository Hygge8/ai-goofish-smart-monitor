# ai-goofish-smart-monitor

闲鱼 AI 智能监控助手，面向全品类商品监控，不再限定摩托车。支持关键词任务、价格区间过滤、包含词 / 排除词过滤、SQLite 去重、钉钉机器人图文卡片通知和 Web 状态页。

重点解决：

- 通知不能只发一长串链接；
- 商品图片要显示在钉钉消息里；
- 电脑端链接和手机端链接不要堆在正文里；
- 只保留按钮入口，例如“立即查看”“发起聊天”；
- 正文只展示商品标题、价格、地区、推荐理由和商家信息。

## 适用场景

可以监控任意关键词，例如：

```text
摩托车、手机、相机、电脑、显卡、家电、家具、乐器、潮玩、二手车、自行车、数码配件
```

## 效果

钉钉通知使用 `actionCard` 图文卡片：

```text
商品图片

闲鱼 AI 智能监控：🚨 新推荐！
类型：新发布  关键词：相机
价格：￥3500  地区：广东
标题：自用索尼 A6400，成色好，配件齐全
推荐理由：价格符合区间，命中“自用、成色好、配件齐全”等关键词。
商家：广东个人玩家

[发起聊天] [立即查看]
```

## 目录结构

```text
ai-goofish-smart-monitor
├── config.example.yaml          # 配置模板
├── docker-compose.yml           # Docker 编排
├── Dockerfile
├── requirements.txt
├── pyproject.toml
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
  - name: 数码相机
    keyword: 索尼相机
    min_price: 1000
    max_price: 8000
    include_words: ["自用", "成色好", "配件齐全"]
    exclude_words: ["故障", "维修", "进水"]

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

### 4. 搜索测试

```bash
python -m goofish_monitor.cli search --keyword 相机 --limit 5
```

### 5. 开始监控

```bash
python -m goofish_monitor.cli run --config config.yaml
```

### 6. Web 状态页

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

本项目优先使用闲鱼页面里抓到的商品首图 `image_url`。如果后面把图片下载到本地，钉钉无法直接显示本地路径，需要配置 OSS、图床或自己的静态文件服务器。

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
python -m goofish_monitor.cli search --keyword 相机 --limit 5
```

确认能抓到标题、价格、图片、链接后，再开启钉钉推送。
