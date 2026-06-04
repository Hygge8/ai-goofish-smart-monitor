from __future__ import annotations

from .config import TaskConfig
from .models import GoofishItem


def analyze_item(item: GoofishItem, task: TaskConfig) -> tuple[bool, str]:
    """规则推荐。后续可接 OpenAI 兼容接口。"""
    title = item.title or ""
    desc = item.description or ""
    text = f"{title} {desc} {item.seller_name} {item.location}"

    if item.price is not None:
        if item.price < task.min_price or item.price > task.max_price:
            return False, f"价格 {item.price:g} 不在配置区间 {task.min_price:g}-{task.max_price:g} 内。"

    hit_exclude = [w for w in task.exclude_words if w and w in text]
    if hit_exclude:
        return False, "命中排除词：" + "、".join(hit_exclude)

    hit_include = [w for w in task.include_words if w and w in text]
    parts = []
    if hit_include:
        parts.append("命中关键词：" + "、".join(hit_include[:5]))
    if item.price is not None:
        parts.append(f"价格 ￥{item.price:g} 符合设定区间")
    if item.location:
        parts.append(f"地区：{item.location}")
    if not parts:
        parts.append("标题与价格符合监控条件")

    reason = "；".join(parts) + "。"
    return True, reason
