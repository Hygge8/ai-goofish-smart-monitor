from __future__ import annotations

import asyncio
import logging

from .ai import analyze_item
from .config import AppConfig
from .db import SeenStore
from .notifier.dingtalk import send_action_card
from .price_watch import detect_price_drop
from .scraper import GoofishScraper

logger = logging.getLogger(__name__)


async def run_once(config: AppConfig) -> int:
    store = SeenStore(config.storage_db)
    scraper = GoofishScraper(headless=config.headless, user_data_dir=config.user_data_dir)
    sent_count = 0

    for task in config.tasks:
        logger.info("开始搜索任务：%s / %s", task.name, task.keyword)
        items = await scraper.search(task.keyword, config.max_items_per_keyword)
        logger.info("任务 %s 抓到 %s 条商品", task.name, len(items))

        for item in items:
            previous_price = store.previous_price(item.item_id)
            price_drop = detect_price_drop(item, task, previous_price)
            store.record_price(item.to_dict())

            ok, reason, score = analyze_item(item, task)
            item_dict = item.to_dict()
            item_dict["reason"] = reason
            item_dict["score"] = score
            item_dict["total_score"] = score.get("total_score")
            item_dict["price_drop"] = price_drop.to_dict()

            already_seen = store.has_seen(item.item_id)
            store.mark_seen(item_dict)

            if price_drop.is_drop and config.dingtalk_enabled:
                drop_reason = f"降价提醒：{price_drop.reason} 原推荐理由：{reason}"
                item_dict["alert_type"] = "price_drop"
                item_dict["reason"] = drop_reason
                logger.info("推送降价商品：%s，%s", item.title, price_drop.reason)
                send_action_card(config.dingtalk_webhook, config.dingtalk_secret, item_dict, drop_reason)
                sent_count += 1
                continue

            if already_seen:
                continue

            if not ok:
                logger.info("跳过商品：%s，原因：%s", item.title, reason)
                continue

            if config.dingtalk_enabled:
                item_dict["alert_type"] = "new_recommendation"
                logger.info("推送商品：%s", item.title)
                send_action_card(config.dingtalk_webhook, config.dingtalk_secret, item_dict, reason)
                sent_count += 1

    return sent_count


async def run_forever(config: AppConfig) -> None:
    if not config.tasks:
        raise ValueError("config.yaml 中没有配置 tasks")

    while True:
        try:
            sent = await run_once(config)
            logger.info("本轮推送 %s 条", sent)
        except Exception:
            logger.exception("监控执行失败")
        await asyncio.sleep(config.interval_seconds)
