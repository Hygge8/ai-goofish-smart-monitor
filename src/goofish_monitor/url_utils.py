from __future__ import annotations

import re
from urllib.parse import parse_qs, quote, urlparse


def extract_item_id(url_or_text: str) -> str:
    if not url_or_text:
        return ""

    text = str(url_or_text)
    patterns = [
        r"[?&]id=(\d+)",
        r"[?&]itemId=(\d+)",
        r"[?&]item_id=(\d+)",
        r"/item/(\d+)",
        r"item\D+(\d{8,})",
        r"(\d{10,})",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return ""


def normalize_item_link(raw_link: str, item_id: str = "") -> str:
    item_id = item_id or extract_item_id(raw_link)
    if item_id:
        return f"https://www.goofish.com/item?id={item_id}"
    return raw_link or "https://www.goofish.com/"


def build_mobile_share_link(raw_link: str, item_id: str = "") -> str:
    item_id = item_id or extract_item_id(raw_link)
    if not item_id:
        return normalize_item_link(raw_link, item_id)
    encoded = quote(f"{{\"id\":\"{item_id}\"}}")
    return (
        "https://pages.goofish.com/sharexy?"
        "loadingVisible=false&bft=item&bfs=idlepc.item&spm=a21ybx.item.0.0"
        f"&bfp={encoded}"
    )


def clean_long_url_from_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"https?://\S+", "", str(text))
    text = re.sub(r"手机端链接[:：]?", "", text)
    text = re.sub(r"电脑端链接[:：]?", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def query_param(url: str, name: str) -> str:
    try:
        parsed = urlparse(url)
        values = parse_qs(parsed.query).get(name)
        return values[0] if values else ""
    except Exception:
        return ""
