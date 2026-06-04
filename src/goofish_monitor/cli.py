from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path

from .config import load_config
from .monitor import run_forever, run_once
from .notifier.dingtalk import send_action_card
from .scraper import search_sync


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def cmd_search(args) -> None:
    config = load_config(args.config)
    items = search_sync(
        keyword=args.keyword,
        limit=args.limit,
        headless=config.headless,
        user_data_dir=config.user_data_dir,
    )
    print(json.dumps([item.to_dict() for item in items], ensure_ascii=False, indent=2))


def cmd_test_dingtalk(args) -> None:
    config = load_config(args.config)
    item = {
        "item_id": "1055857694776",
        "title": "自用23年准信5000公里实表赛科龙ra2，250排量车子无事故",
        "price": 5000,
        "location": "广东",
        "seller_name": "广东个人玩家",
        "keyword": "摩托车",
        "reason": "这是一条测试通知，用于验证推送渠道是否可用；正文不再展示长链接，链接只放到按钮里。",
        "image_url": "https://img.alicdn.com/imgextra/i4/O1CN01XJcqC91wGp5h56i7J_!!6000000006354-2-tps-800-800.png",
        "item_link": "https://www.goofish.com/item?id=1055857694776",
        "chat_link": "https://www.goofish.com/item?id=1055857694776",
    }
    result = send_action_card(config.dingtalk_webhook, config.dingtalk_secret, item, item["reason"])
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_run_once(args) -> None:
    config = load_config(args.config)
    sent = asyncio.run(run_once(config))
    print(f"本轮推送 {sent} 条")


def cmd_run(args) -> None:
    config = load_config(args.config)
    asyncio.run(run_forever(config))


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="闲鱼摩托车监控助手")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")

    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="搜索商品并打印 JSON")
    p_search.add_argument("--keyword", default="摩托车")
    p_search.add_argument("--limit", type=int, default=5)
    p_search.set_defaults(func=cmd_search)

    p_test = sub.add_parser("test-dingtalk", help="发送一条钉钉图文卡片测试消息")
    p_test.set_defaults(func=cmd_test_dingtalk)

    p_once = sub.add_parser("run-once", help="执行一轮监控")
    p_once.set_defaults(func=cmd_run_once)

    p_run = sub.add_parser("run", help="持续监控")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
