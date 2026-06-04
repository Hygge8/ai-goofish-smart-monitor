param(
  [string]$BackupRoot = "backups"
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = Join-Path $BackupRoot "local-runtime-$timestamp"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$items = @(
  ".env",
  "config.json",
  "xianyu_state.json",
  "state",
  "data",
  "jsonl",
  "images",
  "logs",
  "prompts",
  "price_history"
)

foreach ($item in $items) {
  if (Test-Path $item) {
    Copy-Item -Path $item -Destination $backupDir -Recurse -Force
    Write-Host "已备份 $item"
  }
}

Write-Host "备份完成：$backupDir"
