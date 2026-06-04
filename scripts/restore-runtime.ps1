param(
  [Parameter(Mandatory=$true)]
  [string]$BackupDir
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupDir)) {
  throw "备份目录不存在：$BackupDir"
}

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
  $source = Join-Path $BackupDir $item
  if (Test-Path $source) {
    Copy-Item -Path $source -Destination "." -Recurse -Force
    Write-Host "已恢复 $item"
  }
}

Write-Host "恢复完成：$BackupDir"
