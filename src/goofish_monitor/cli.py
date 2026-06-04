from __future__ import annotations

import argparse
import asyncio
import json
import logging

from .account import AccountStore
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
    account_state = None
    user_data_dir = config.user_data_dir
    if args.account:
        account_state = AccountStore(config.account_dir).load(args.account)
        user_data_dir = f"{config.user_data_dir}/{args.account}"
        if not account_state:
            raise FileNotFoundError(f"未找到账号登录态：{args.account}，请先导入登录态")

    items = search_sync(
        keyword=args.keyword,
        limit=args.limit,
        headless=config.headless,
        user_data_dir=user_data_dir,
        account_state=account_state,
    )
    print(json.dumps([item.to_dict() for item in items], ensure_ascii=False, indent=2))


def cmd_import_account(args) -> None:
    config = load_config(args.config)
    store = AccountStore(config.account_dir)
    path = store.import_from_file(args.name, args.file)
    print(f"账号登录态已导入：{args.name} -> {path}")


def cmd_list_accounts(args) -> None:
    config = load_config(args.config)
    accounts = AccountStore(config.account_dir).list_accounts()
    if not accounts:
        print("暂无账号登录态。")
        return
    for name in accounts:
        print(name)


def cmd_test_dingtalk(args) -> None:
    config = load_config(args.config)
    item = {
        "item_id": "1055857694776",
        "title": "自用索尼 A6400，成色好，配件齐全",
        "price": 3500,
        "location": "广东",
        "seller_name": "广东个人玩家",
        "keyword": "相机",
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
    parser = argparse.ArgumentParser(description="闲鱼 AI 智能监控助手")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")

    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="搜索商品并打印 JSON")
    p_search.add_argument("--keyword", default="相机")
    p_search.add_argument("--limit", type=int, default=5)
    p_search.add_argument("--account", default="", help="使用指定账号登录态")
    p_search.set_defaults(func=cmd_search)

    p_import = sub.add_parser("import-account", help="导入账号登录态 JSON")
    p_import.add_argument("--name", required=True, help="账号名称，例如 acc1")
    p_import.add_argument("--file", required=True, help="登录态 JSON 文件路径")
    p_import.set_defaults(func=cmd_import_account)

    p_accounts = sub.add_parser("list-accounts", help="列出已导入账号")
    p_accounts.set_defaults(func=cmd_list_accounts)

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
