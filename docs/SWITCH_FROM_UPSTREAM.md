# 从上游 Usagi 版本切换到修复版

如果你之前安装的是：

```text
https://github.com/Usagi-org/ai-goofish-monitor
```

现在想直接切换到本仓库修复版：

```text
https://github.com/Hygge8/ai-goofish-smart-monitor
```

可以在原目录内直接切换远程仓库，不需要重新安装，也可以保留你之前配置好的任务、账号登录态、通知配置和历史结果。

## 修复版包含什么

本仓库在 Usagi 底座基础上增加了：

```text
钉钉 ActionCard 图文卡片
商品图片展示
商品链接按钮化
修复版 Docker 文档
本地数据备份脚本
钉钉通知设置扩展
项目名 ai-goofish-smart-monitor
```

## Linux / macOS 操作步骤

### 1. 进入你现在安装的目录

```bash
cd ai-goofish-monitor
```

### 2. 停止服务

```bash
docker compose down
```

### 3. 备份本地数据

```bash
mkdir -p ../goofish-backup

cp -a .env ../goofish-backup/ 2>/dev/null || true
cp -a data ../goofish-backup/ 2>/dev/null || true
cp -a state ../goofish-backup/ 2>/dev/null || true
cp -a prompts ../goofish-backup/ 2>/dev/null || true
cp -a logs ../goofish-backup/ 2>/dev/null || true
cp -a images ../goofish-backup/ 2>/dev/null || true
cp -a jsonl ../goofish-backup/ 2>/dev/null || true
cp -a price_history ../goofish-backup/ 2>/dev/null || true
cp -a config.json ../goofish-backup/ 2>/dev/null || true
```

这些目录一般包含：

```text
.env                 AI、通知、Web 登录等配置
data/                SQLite 数据库、任务、结果
state/               闲鱼账号登录态
prompts/             Prompt 配置
logs/                运行日志
images/              商品图片缓存
jsonl/               旧版结果数据
price_history/       旧版价格历史
config.json          旧版任务配置兼容文件
```

### 4. 切换到修复版仓库

```bash
git remote remove origin
git remote add origin https://github.com/Hygge8/ai-goofish-smart-monitor.git
git fetch origin main
git reset --hard origin/main
```

### 5. 恢复本地数据

```bash
cp -a ../goofish-backup/.env . 2>/dev/null || true
cp -a ../goofish-backup/data . 2>/dev/null || true
cp -a ../goofish-backup/state . 2>/dev/null || true
cp -a ../goofish-backup/prompts . 2>/dev/null || true
cp -a ../goofish-backup/logs . 2>/dev/null || true
cp -a ../goofish-backup/images . 2>/dev/null || true
cp -a ../goofish-backup/jsonl . 2>/dev/null || true
cp -a ../goofish-backup/price_history . 2>/dev/null || true
cp -a ../goofish-backup/config.json . 2>/dev/null || true
```

### 6. 重新构建并启动

```bash
docker compose up -d --build
docker compose logs -f app
```

### 7. 打开后台

```text
http://127.0.0.1:8000
```

## Windows PowerShell 操作步骤

### 1. 进入项目目录并停止服务

```powershell
cd ai-goofish-monitor
docker compose down
```

### 2. 备份本地数据

```powershell
New-Item -ItemType Directory -Force ..\goofish-backup

Copy-Item .env ..\goofish-backup\ -Force -ErrorAction SilentlyContinue
Copy-Item data ..\goofish-backup\ -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item state ..\goofish-backup\ -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item prompts ..\goofish-backup\ -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item logs ..\goofish-backup\ -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item images ..\goofish-backup\ -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item jsonl ..\goofish-backup\ -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item price_history ..\goofish-backup\ -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item config.json ..\goofish-backup\ -Force -ErrorAction SilentlyContinue
```

### 3. 切换到修复版仓库

```powershell
git remote remove origin
git remote add origin https://github.com/Hygge8/ai-goofish-smart-monitor.git
git fetch origin main
git reset --hard origin/main
```

### 4. 恢复本地数据

```powershell
Copy-Item ..\goofish-backup\.env . -Force -ErrorAction SilentlyContinue
Copy-Item ..\goofish-backup\data . -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ..\goofish-backup\state . -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ..\goofish-backup\prompts . -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ..\goofish-backup\logs . -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ..\goofish-backup\images . -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ..\goofish-backup\jsonl . -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ..\goofish-backup\price_history . -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ..\goofish-backup\config.json . -Force -ErrorAction SilentlyContinue
```

### 5. 启动

```powershell
docker compose up -d --build
docker compose logs -f app
```

## 以后如何更新

切换到本仓库后，以后不用再切换远程仓库，直接在当前目录执行：

```bash
git pull origin main
docker compose up -d --build
```

Windows PowerShell：

```powershell
git pull origin main
docker compose up -d --build
```

## 检查当前远程仓库是否正确

```bash
git remote -v
```

应该看到：

```text
origin  https://github.com/Hygge8/ai-goofish-smart-monitor.git (fetch)
origin  https://github.com/Hygge8/ai-goofish-smart-monitor.git (push)
```

## 常见问题

### 1. 任务不见了怎么办？

先检查是否恢复了 `data/` 目录。当前版本任务和结果主要存储在 SQLite 数据库中，默认位置是：

```text
data/app.sqlite3
```

如果你是从旧版迁移，也要保留：

```text
config.json
jsonl/
price_history/
```

应用首次启动时会尝试导入旧数据。

### 2. 登录态不见了怎么办？

检查是否恢复了：

```text
state/
xianyu_state.json
```

如果没有，只能重新在 Web 后台导入闲鱼登录态。

### 3. 钉钉通知没有效果怎么办？

检查 `.env` 或 Web 后台“系统设置 / 通知设置”里的：

```text
DINGTALK_WEBHOOK
DINGTALK_SECRET
```

如果你的钉钉机器人没有开启加签，`DINGTALK_SECRET` 可以留空。

### 4. 拉取后还是上游版本怎么办？

重新检查远程仓库：

```bash
git remote -v
```

如果还是 `Usagi-org/ai-goofish-monitor`，重新执行：

```bash
git remote remove origin
git remote add origin https://github.com/Hygge8/ai-goofish-smart-monitor.git
git fetch origin main
git reset --hard origin/main
```

### 5. 不想原目录切换，想全新安装怎么办？

也可以新建目录安装修复版：

```bash
git clone https://github.com/Hygge8/ai-goofish-smart-monitor.git
cd ai-goofish-smart-monitor
cp .env.example .env
docker compose up -d --build
```

然后手动把旧目录里的 `.env`、`data/`、`state/` 等复制过来。
