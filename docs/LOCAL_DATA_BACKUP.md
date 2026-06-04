# 本地配置与数据保存说明

更新代码前，务必先备份本地运行数据。仓库里的代码可以随时更新，但本地配置、登录态、任务、结果、图片、日志不要跟着代码一起覆盖。

## 哪些文件需要保留

这些是本地运行时数据：

```text
.env
config.json
xianyu_state.json
state/
data/
jsonl/
images/
logs/
prompts/
price_history/
```

仓库的 `.gitignore` 已经忽略了这些路径，正常 `git pull` 不会覆盖它们。但如果你重新克隆、删除目录、执行强制同步、或者 Docker 容器没有挂载数据目录，这些本地数据仍然可能丢失。

## 推荐更新方式

### Windows PowerShell

```powershell
# 1. 在仓库根目录执行备份
powershell -ExecutionPolicy Bypass -File .\scripts\backup-runtime.ps1

# 2. 拉取最新代码
git pull origin main

# 3. 如果发现配置丢失，从 backups 目录恢复
powershell -ExecutionPolicy Bypass -File .\scripts\restore-runtime.ps1 -BackupDir .\backups\local-runtime-YYYYMMDD-HHMMSS
```

### Linux / macOS

```bash
# 1. 在仓库根目录执行备份
bash scripts/backup-runtime.sh

# 2. 拉取最新代码
git pull origin main

# 3. 如果发现配置丢失，从 backups 目录恢复
bash scripts/restore-runtime.sh backups/local-runtime-YYYYMMDD-HHMMSS
```

## 更稳的做法

把运行数据放在仓库外，例如：

```text
D:\goofish-runtime
```

然后每次更新代码只更新仓库目录，运行数据单独保存。Docker 部署时也建议挂载这些目录：

```yaml
volumes:
  - ./runtime/.env:/app/.env
  - ./runtime/config.json:/app/config.json
  - ./runtime/state:/app/state
  - ./runtime/data:/app/data
  - ./runtime/jsonl:/app/jsonl
  - ./runtime/images:/app/images
  - ./runtime/logs:/app/logs
  - ./runtime/prompts:/app/prompts
  - ./runtime/price_history:/app/price_history
```

## 千万不要这样更新

```bash
rm -rf ai-goofish-smart-monitor
git clone https://github.com/Hygge8/ai-goofish-smart-monitor.git
```

这种方式会直接把原来的本地配置和运行数据一起删掉。

如果必须重装，请先把上面列出的运行时文件夹复制到安全位置。
