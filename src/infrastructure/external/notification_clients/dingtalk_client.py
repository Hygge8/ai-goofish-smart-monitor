"""
DingTalk ActionCard notification client.
Sends product image + key fields + buttons, without dumping long URLs into the body.
"""
import asyncio
import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Dict

import requests

from .base import NotificationClient


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
        image_block = f"![商品图片]({message.image_url})\n\n" if message.image_url else ""
        item_url = message.mobile_link or message.desktop_link
        text = (
            f"{image_block}"
            f"### 闲鱼 AI 智能监控：{message.notification_title}\n\n"
            f"价格：{message.price}\n\n"
            f"标题：{message.title}\n\n"
            f"推荐理由：{message.reason}"
        )
        payload = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": f"闲鱼 AI 智能监控：{message.notification_title}",
                "text": text,
                "btnOrientation": "1",
                "btns": [
                    {"title": "发起聊天", "actionURL": item_url},
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
