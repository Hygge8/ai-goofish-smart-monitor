"""
DingTalk ActionCard notification client.

视频同款通知样式：
- 商品主图置顶
- 商品摘要分组展示，正文不展示长链接
- 底部两个按钮：发起聊天、立即查看
"""
import asyncio
import base64
import hashlib
import hmac
import re
import time
import urllib.parse
from typing import Any, Dict

import requests

from .base import NotificationClient


def _text(value: Any, default: str = "-") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _truncate(value: Any, limit: int = 220) -> str:
    text = _text(value, "")
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _normalize_image_url(url: str | None) -> str:
    url = _text(url, "")
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    return url


def _extract_item_id(url: str) -> str:
    if not url:
        return ""
    patterns = [r"[?&]id=(\d+)", r"[?&]itemId=(\d+)", r"itemId=(\d+)", r"item/(\d+)", r"(\d{10,})"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def _build_goofish_item_url(desktop_link: str, mobile_link: str | None) -> str:
    if mobile_link and mobile_link != "#":
        return mobile_link
    if desktop_link and desktop_link != "#":
        return desktop_link
    return "https://www.goofish.com/"


def _build_chat_url(product_data: Dict, item_url: str) -> str:
    # 如果后续抓取侧能提供聊天链接，这里优先使用；否则使用商品链接兜底。
    for key in ("发起聊天链接", "聊天链接", "chat_link", "mobile_link"):
        value = product_data.get(key)
        if value:
            return str(value)
    return item_url


def _format_tags(tags: Any) -> str:
    if not tags:
        return "-"
    if isinstance(tags, (list, tuple, set)):
        return "、".join(str(item) for item in tags if item) or "-"
    return str(tags)


class DingTalkClient(NotificationClient):
    channel_key = "dingtalk"
    display_name = "钉钉机器人"

    def __init__(self, webhook_url: str | None = None, secret: str | None = None, pcurl_to_mobile: bool = True):
        super().__init__(enabled=bool(webhook_url), pcurl_to_mobile=pcurl_to_mobile)
        self.webhook_url = webhook_url
        self.secret = secret or ""

    async def send(self, product_data: Dict, reason: str) -> None:
        if not self.is_enabled():
            raise RuntimeError("钉钉机器人未启用")

        message = self._build_message(product_data, reason)
        item_url = _build_goofish_item_url(message.desktop_link, message.mobile_link)
        chat_url = _build_chat_url(product_data, item_url)
        image_url = _normalize_image_url(message.image_url)

        title = _truncate(message.title, 80)
        price = _text(message.price)
        original_price = _text(product_data.get("商品原价"), "")
        area = _text(product_data.get("发货地区") or product_data.get("地区") or product_data.get("位置"))
        seller = _text(product_data.get("卖家昵称") or product_data.get("卖家") or product_data.get("seller_name"))
        publish_time = _text(product_data.get("发布时间"), "未知")
        want_count = _text(product_data.get("“想要”人数") or product_data.get("想要人数"), "-")
        browse_count = _text(product_data.get("浏览量"), "-")
        item_id = _text(product_data.get("商品ID") or _extract_item_id(message.desktop_link), "-")
        tags = _format_tags(product_data.get("商品标签"))
        reason_text = _truncate(message.reason, 360)

        image_block = f"![商品图片]({image_url})\n\n" if image_url.startswith("http") else ""
        original_price_line = f"原价：{original_price}\n\n" if original_price and original_price != "暂无" else ""
        tags_line = f"标签：{tags}\n\n" if tags != "-" else ""

        text = (
            f"{image_block}"
            f"### 闲鱼 AI 智能监控：🚨 新推荐！\n\n"
            f"**{title}**\n\n"
            f"价格：**{price}**\n\n"
            f"{original_price_line}"
            f"地区：{area}  ｜  发布时间：{publish_time}\n\n"
            f"卖家：{seller}  ｜  想要：{want_count}  ｜  浏览：{browse_count}\n\n"
            f"{tags_line}"
            f"商品ID：{item_id}\n\n"
            f"推荐理由：{reason_text}"
        )

        payload = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": f"闲鱼 AI 智能监控：🚨 新推荐！{title}",
                "text": text,
                "btnOrientation": "1",
                "btns": [
                    {"title": "发起聊天", "actionURL": chat_url},
                    {"title": "立即查看", "actionURL": item_url},
                ],
            },
        }

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(self._signed_url(), json=payload, timeout=15),
        )
        response.raise_for_status()
        result = response.json()
        if result.get("errcode", 0) != 0:
            raise RuntimeError(result.get("errmsg", "钉钉返回未知错误"))

    def _signed_url(self) -> str:
        if not self.secret:
            return self.webhook_url
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"
        digest = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(digest))
        joiner = "&" if "?" in self.webhook_url else "?"
        return f"{self.webhook_url}{joiner}timestamp={timestamp}&sign={sign}"
