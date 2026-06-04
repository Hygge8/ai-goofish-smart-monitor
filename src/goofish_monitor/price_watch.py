from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .config import TaskConfig
from .models import GoofishItem


@dataclass
class PriceDropResult:
    is_drop: bool
    previous_price: float | None
    current_price: float | None
    drop_amount: float = 0
    drop_ratio: float = 0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_price_drop(item: GoofishItem, task: TaskConfig, previous_price: float | None) -> PriceDropResult:
    current = item.price
    if not task.notify_price_drop:
        return PriceDropResult(False, previous_price, current, reason="任务未开启降价提醒")
    if previous_price is None or current is None:
        return PriceDropResult(False, previous_price, current, reason="缺少历史价格或当前价格")
    if previous_price <= 0 or current >= previous_price:
        return PriceDropResult(False, previous_price, current, reason="未发生降价")

    drop_amount = previous_price - current
    drop_ratio = drop_amount / previous_price
    is_drop = drop_amount >= task.price_drop_amount or drop_ratio >= task.price_drop_ratio
    reason = (
        f"价格从 ￥{previous_price:g} 降到 ￥{current:g}，"
        f"下降 ￥{drop_amount:g}，降幅 {drop_ratio:.1%}。"
    )
    if not is_drop:
        reason += f"未达到提醒阈值：￥{task.price_drop_amount:g} 或 {task.price_drop_ratio:.1%}。"
    return PriceDropResult(
        is_drop=is_drop,
        previous_price=previous_price,
        current_price=current,
        drop_amount=round(drop_amount, 2),
        drop_ratio=round(drop_ratio, 4),
        reason=reason,
    )
