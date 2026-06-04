from __future__ import annotations

import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Any

import requests


def build_signed_url(webhook: str, secret: str = "") -> str:
    if not secret:
        return webhook
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    digest = hmac.new(secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(digest))
    joiner = "&" if "?" in webhook else "?"
    return f"{webhook}{joiner}timestamp={timestamp}&sign={sign}"


def send_action_card(webhook: str, secret: str, item: dict[str, Any], reason: str = "") -> dict[str, Any]:
    if not webhook:
        raise ValueError("未配置 DINGTALK_WEBHOOK")

    title = str(item.get("title") or "闲鱼商品")
    price = item.get("price")
    price_text = "未知" if price in (None, "") else f"￥{price}"
    location = str(item.get("location") or "未知")
    seller_name = str(item.get("seller_name") or "未知")
    image_url = str(item.get("image_url") or "")
    item_link = str(item.get("item_link") or "https://www.goofish.com/")
    chat_link = str(item.get("chat_link") or item_link)
    keyword = str(item.get("keyword") or "闲鱼")
    reason = reason or str(item.get("reason") or "符合监控条件")

    image_block = f"![商品图片]({image_url})\n\n" if image_url.startswith("http") else ""
    text = (
        f"{image_block}"
        f"### 闲鱼 AI 智能监控：🚨 新推荐！\n\n"
        f"类型：新发布  关键词：{keyword}\n\n"
        f"价格：{price_text}  地区：{location}\n\n"
        f"标题：{title}\n\n"
        f"推荐理由：{reason}\n\n"
        f"商家：{seller_name}"
    )

    payload = {
        "msgtype": "actionCard",
        "actionCard": {
            "title": f"闲鱼 AI 智能监控：🚨 新推荐！{title}",
            "text": text,
            "btnOrientation": "1",
            "btns": [
                {"title": "发起聊天", "actionURL": chat_link},
                {"title": "立即查看", "actionURL": item_link},
            ],
        },
    }

    url = build_signed_url(webhook, secret)
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def send_markdown_fallback(webhook: str, secret: str, item: dict[str, Any], reason: str = "") -> dict[str, Any]:
    title = str(item.get("title") or "闲鱼商品")
    item_link = str(item.get("item_link") or "https://www.goofish.com/")
    price = item.get("price", "未知")
    reason = reason or str(item.get("reason") or "符合监控条件")
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"闲鱼 AI 智能监控：{title}",
            "text": f"### 闲鱼 AI 智能监控：{title}\n\n价格：{price}\n\n推荐理由：{reason}\n\n[立即查看]({item_link})",
        },
        "at": {"isAtAll": False},
    }
    resp = requests.post(build_signed_url(webhook, secret), json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()
