from __future__ import annotations

from .config import TaskConfig
from .models import GoofishItem
from .scorer import score_item


def analyze_item(item: GoofishItem, task: TaskConfig) -> tuple[bool, str, dict]:
    """透明评分推荐。

    返回：是否推荐、推荐理由、评分明细。
    """
    score = score_item(item, task)
    score_dict = score.to_dict()

    ok = score.total_score >= task.min_score and not score.exclude_hits

    reason_parts = [
        f"综合评分 {score.total_score}/100，阈值 {task.min_score:g}",
        *score.reasons[:4],
    ]
    if score.risk_tags:
        reason_parts.append("风险标签：" + "、".join(score.risk_tags[:6]))
    if not ok:
        reason_parts.append("未达到推荐条件，仅记录不推送")

    return ok, "；".join(reason_parts) + "。", score_dict
