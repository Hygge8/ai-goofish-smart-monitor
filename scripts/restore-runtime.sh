#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${1:-}"
if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
  echo "用法：bash scripts/restore-runtime.sh backups/local-runtime-YYYYMMDD-HHMMSS"
  exit 1
fi

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
  if [ -e "$BACKUP_DIR/$item" ]; then
    cp -a "$BACKUP_DIR/$item" .
    echo "已恢复 $item"
  fi
done

echo "恢复完成：$BACKUP_DIR"
