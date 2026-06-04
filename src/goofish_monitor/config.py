from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
import os


@dataclass
class TaskConfig:
    name: str
    keyword: str
    min_price: float = 0
    max_price: float = 99999999
    include_words: list[str] = field(default_factory=list)
    exclude_words: list[str] = field(default_factory=list)


@dataclass
class AppConfig:
    interval_seconds: int = 60
    headless: bool = True
    max_items_per_keyword: int = 20
    storage_db: str = "data/goofish.db"
    user_data_dir: str = "state/browser"
    dingtalk_enabled: bool = True
    tasks: list[TaskConfig] = field(default_factory=list)
    dingtalk_webhook: str = ""
    dingtalk_secret: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"


def load_config(path: str = "config.yaml") -> AppConfig:
    load_dotenv()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}，请复制 config.example.yaml 为 config.yaml")

    raw: dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    monitor = raw.get("monitor", {}) or {}
    dingtalk = raw.get("dingtalk", {}) or {}

    tasks = []
    for item in raw.get("tasks", []) or []:
        tasks.append(TaskConfig(
            name=str(item.get("name") or item.get("keyword") or "默认任务"),
            keyword=str(item.get("keyword") or item.get("name") or "摩托车"),
            min_price=float(item.get("min_price", 0) or 0),
            max_price=float(item.get("max_price", 99999999) or 99999999),
            include_words=list(item.get("include_words", []) or []),
            exclude_words=list(item.get("exclude_words", []) or []),
        ))

    return AppConfig(
        interval_seconds=int(monitor.get("interval_seconds", 60)),
        headless=bool(monitor.get("headless", True)),
        max_items_per_keyword=int(monitor.get("max_items_per_keyword", 20)),
        storage_db=str(monitor.get("storage_db", "data/goofish.db")),
        user_data_dir=str(monitor.get("user_data_dir", "state/browser")),
        dingtalk_enabled=bool(dingtalk.get("enabled", True)),
        tasks=tasks,
        dingtalk_webhook=os.getenv("DINGTALK_WEBHOOK", ""),
        dingtalk_secret=os.getenv("DINGTALK_SECRET", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )
