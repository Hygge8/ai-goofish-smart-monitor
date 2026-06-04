from __future__ import annotations

import asyncio
import logging

from .account import AccountStore
from .ai import analyze_item
from .config import AppConfig, TaskConfig
from .db import SeenStore
from .errors import SearchBlockedError
from .notifier.dingtalk import send_action_card
from .price_watch import detect_price_drop
from .scraper import GoofishScraper

logger = logging.getLogger(__name__)


def _candidate_accounts(task: TaskConfig, accounts: AccountStore) -> list[str]:
    names = []
    if task.account:
        names.append(task.account)
    for name in accounts.list_accounts():
        if name not in names:
            names.append(name)
    return names or [""]


async def _search_with_account_retry(config: AppConfig, task: TaskConfig, accounts: AccountStore):
    last_error: Exception | None = None
    for account_name in _candidate_accounts(task, accounts):
        account_state = accounts.load(account_name) if account_name else None
        if account_name and not account_state:
            logger.warning("任务 %s 配置了账号 %s，但未找到登录态文件", task.name, account_name)
            accounts.mark_status(account_name, "missing", "未找到登录态文件")
            continue

        scraper = GoofishScraper(
            headless=config.headless,
            user_data_dir=f"{config.user_data_dir}/{account_name or 'default'}",
            account_state=account_state,
        )
        try:
            items = await scraper.search(task.keyword, config.max_items_per_keyword)
            if account_name:
                accounts.mark_status(account_name, "ok", f"任务 {task.name} 搜索成功，抓到 {len(items)} 条")
            return account_name, items
        except SearchBlockedError as exc:
            last_error = exc
            if account_name:
                accounts.mark_status(account_name, "blocked", str(exc))
            logger.warning("账号 %s 搜索任务 %s 被拦截，准备尝试下一个账号：%s", account_name or "default", task.name, exc)
            continue

    if last_error:
        raise last_error
    return "", []


async def run_once(config: AppConfig) -> int:
    store = SeenStore(config.storage_db)
    accounts = AccountStore(config.account_dir)
    sent_count = 0

    for task in config.tasks:
        logger.info("开始搜索任务：%s / %s", task.name, task.keyword)
        used_account, items = await _search_with_account_retry(config, task, accounts)
        logger.info("任务 %s 使用账号 %s 抓到 %s 条商品", task.name, used_account or "default", len(items))

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
            item_dict["account"] = used_account

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
