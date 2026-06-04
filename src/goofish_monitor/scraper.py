from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import async_playwright

from .errors import SearchBlockedError
from .models import GoofishItem
from .url_utils import extract_item_id, normalize_item_link, build_mobile_share_link


BLOCK_KEYWORDS = [
    "登录", "验证码", "安全验证", "滑块", "访问受限", "操作太频繁", "网络繁忙",
    "请稍后再试", "验证一下", "账号异常", "风险", "人机验证",
]


def _to_float(value: str) -> float | None:
    if value is None:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", str(value).replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _pick_image(raw: str) -> str:
    if not raw:
        return ""
    if raw.startswith("//"):
        return "https:" + raw
    if raw.startswith("http"):
        return raw
    return raw


class GoofishScraper:
    def __init__(
        self,
        headless: bool = True,
        user_data_dir: str = "state/browser",
        account_state: dict | None = None,
    ):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.account_state = account_state or {}

    async def search(self, keyword: str, limit: int = 20) -> list[GoofishItem]:
        url = f"https://www.goofish.com/search?q={quote(keyword)}"
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=self.headless,
                viewport={"width": 1366, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            try:
                if self.account_state.get("cookies"):
                    await context.add_cookies(self.account_state["cookies"])

                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)

                await self._check_blocked(page)

                for _ in range(3):
                    await page.mouse.wheel(0, 1600)
                    await page.wait_for_timeout(1200)

                items = await self._extract_from_page(page, keyword, limit)
                if not items:
                    await self._check_blocked(page)
                return items
            finally:
                await context.close()

    async def _check_blocked(self, page) -> None:
        title = ""
        text = ""
        try:
            title = await page.title()
            text = await page.locator("body").inner_text(timeout=3000)
        except Exception:
            return
        combined = f"{title}\n{text}"[:3000]
        if any(word in combined for word in BLOCK_KEYWORDS):
            raise SearchBlockedError("页面疑似被登录、验证码、风控或异常提示拦截")

    async def _extract_from_page(self, page, keyword: str, limit: int) -> list[GoofishItem]:
        js = """
        () => {
          const nodes = Array.from(document.querySelectorAll('a[href*="item"], div[class*="item"], div[class*="card"], div[class*="feeds"]'));
          const results = [];
          const seen = new Set();
          for (const node of nodes) {
            const a = node.matches('a') ? node : node.querySelector('a[href*="item"]');
            const href = a ? a.href : '';
            const text = (node.innerText || '').trim();
            const img = node.querySelector('img');
            const image = img ? (img.src || img.getAttribute('data-src') || img.getAttribute('data-ks-lazyload')) : '';
            if (!href && !text) continue;
            const key = href || text.slice(0, 80);
            if (seen.has(key)) continue;
            seen.add(key);
            results.push({href, text, image});
          }
          return results.slice(0, 80);
        }
        """
        raw_cards = await page.evaluate(js)
        parsed: list[GoofishItem] = []
        for card in raw_cards:
            href = str(card.get("href") or "")
            text = str(card.get("text") or "").strip()
            image = _pick_image(str(card.get("image") or ""))
            item_id = extract_item_id(href or text)
            if not item_id and not href:
                continue

            lines = [line.strip() for line in text.splitlines() if line.strip()]
            title = lines[0] if lines else "闲鱼商品"
            price = None
            location = ""
            seller_name = ""

            for line in lines:
                if price is None and ("￥" in line or "¥" in line or re.search(r"\b\d{3,}\b", line)):
                    price = _to_float(line)
                if not location and re.search(r"北京|上海|广州|深圳|广东|浙江|江苏|山东|河南|河北|四川|重庆|湖北|湖南|福建|广西|云南|陕西|辽宁|天津|山西|安徽|江西|贵州|海南|甘肃|新疆|内蒙古|黑龙江|吉林|宁夏|青海|西藏", line):
                    location = line[:20]

            item_link = normalize_item_link(href, item_id)
            chat_link = build_mobile_share_link(item_link, item_id)
            parsed.append(GoofishItem(
                item_id=item_id or item_link,
                title=title,
                price=price,
                location=location,
                seller_name=seller_name,
                image_url=image,
                item_link=item_link,
                chat_link=chat_link,
                description=text,
                keyword=keyword,
            ))
            if len(parsed) >= limit:
                break
        return parsed


def search_sync(
    keyword: str,
    limit: int = 20,
    headless: bool = True,
    user_data_dir: str = "state/browser",
    account_state: dict | None = None,
) -> list[GoofishItem]:
    import asyncio

    return asyncio.run(
        GoofishScraper(
            headless=headless,
            user_data_dir=user_data_dir,
            account_state=account_state,
        ).search(keyword, limit)
    )
