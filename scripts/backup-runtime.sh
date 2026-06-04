#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="${1:-backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/local-runtime-$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

ITEMS=(
  ".env"
  "config.json"
  "xianyu_state.json"
  "state"
  "data"
  "jsonl"
  "images"
  "logs"
  "prompts"
  "price_history"
)

for item in "${ITEMS[@]}"; do
  if [ -e "$item" ]; then
    cp -a "$item" "$BACKUP_DIR/"
    echo "已备份 $item"
  fi
done

echo "备份完成：$BACKUP_DIR"
