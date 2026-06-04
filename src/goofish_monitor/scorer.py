from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .config import TaskConfig
from .models import GoofishItem


@dataclass
class ScoreBreakdown:
    total_score: float
    text_score: float
    price_score: float
    seller_score: float
    vision_score: float
    confidence_score: float
    risk_penalty: float
    include_hits: list[str]
    exclude_hits: list[str]
    risk_tags: list[str]
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def _contains_any(text: str, words: list[str]) -> list[str]:
    return [word for word in words if word and word in text]


def score_item(item: GoofishItem, task: TaskConfig) -> ScoreBreakdown:
    """轻量三维评分：规则文本 + 卖家/风险 + 图片可信度。

    设计目标：
    - 保留 Usagi 的多任务、价格、关键词规则思路；
    - 借鉴 QB 的“评分看板”思想，但避免上来就依赖复杂数据库和重模型；
    - 先给出透明、可解释、可调权重的轻量评分，后续可替换为真正的多模态模型。
    """

    title = item.title or ""
    desc = item.description or ""
    seller = item.seller_name or ""
    location = item.location or ""
    text = f"{title} {desc} {seller} {location}"

    include_hits = _contains_any(text, task.include_words)
    exclude_hits = _contains_any(text, task.exclude_words)

    risk_words = ["事故", "水泡", "抵押", "报废", "故障", "进水", "维修", "翻新", "监管", "贷款", "分期"]
    risk_tags = _contains_any(text, risk_words)

    reasons: list[str] = []

    # 1. 文本匹配分：命中用户想要的关键词越多越高。
    if task.include_words:
        text_score = 40 + 60 * min(len(include_hits) / max(len(task.include_words), 1), 1)
    else:
        text_score = 65
    if include_hits:
        reasons.append("命中偏好词：" + "、".join(include_hits[:6]))

    # 2. 价格分：在区间内满分；越接近区间边界外，分数越低。
    if item.price is None:
        price_score = 50
        reasons.append("价格未识别，按中性分处理")
    elif task.min_price <= item.price <= task.max_price:
        price_score = 100
        reasons.append(f"价格 ￥{item.price:g} 在区间 {task.min_price:g}-{task.max_price:g} 内")
    else:
        # 超出价格区间直接强烈降分，但不在这里硬拒绝，交给 analyze_item 决策。
        center = (task.min_price + task.max_price) / 2 or 1
        distance = abs(item.price - center) / max(center, 1)
        price_score = _clamp(60 - distance * 60)
        reasons.append(f"价格 ￥{item.price:g} 不在区间 {task.min_price:g}-{task.max_price:g} 内")

    # 3. 卖家/交易可信度：优先个人自用、描述清楚；惩罚车商/贩子/批量。
    seller_score = 60
    positive_seller_words = ["个人", "自用", "一手", "闲置", "实拍", "原图", "配件齐全", "发票", "保修"]
    negative_seller_words = ["商家", "贩子", "批发", "回收", "置换", "全新未拆批量", "引流"]
    positive_seller_hits = _contains_any(text, positive_seller_words)
    negative_seller_hits = _contains_any(text, negative_seller_words)
    seller_score += min(len(positive_seller_hits) * 8, 32)
    seller_score -= min(len(negative_seller_hits) * 12, 36)
    seller_score = _clamp(seller_score)
    if positive_seller_hits:
        reasons.append("卖家/描述正向信号：" + "、".join(positive_seller_hits[:5]))
    if negative_seller_hits:
        risk_tags.extend(negative_seller_hits)

    # 4. 图片可信度：先用轻量启发式，后续可以替换为真正视觉模型。
    vision_score = 50
    if item.image_url.startswith("http"):
        vision_score += 25
        reasons.append("已抓取商品首图，可用于图文卡片展示")
    if any(word in text for word in ["实拍", "原图", "细节图", "多图", "成色"]):
        vision_score += 15
    if any(word in text for word in ["网图", "盗图", "仅展示", "图片不符"]):
        vision_score -= 25
        risk_tags.append("图片风险")
    vision_score = _clamp(vision_score)

    # 5. 置信度：信息越完整，越可信。
    confidence_score = 35
    if title:
        confidence_score += 15
    if item.price is not None:
        confidence_score += 15
    if location:
        confidence_score += 10
    if item.image_url.startswith("http"):
        confidence_score += 15
    if desc and len(desc) >= 30:
        confidence_score += 10
    confidence_score = _clamp(confidence_score)

    risk_penalty = 0
    if exclude_hits:
        risk_penalty += 45
        reasons.append("命中排除词：" + "、".join(exclude_hits[:6]))
    if risk_tags:
        risk_penalty += min(len(set(risk_tags)) * 8, 35)

    weights = task.score_weights or {}
    text_w = float(weights.get("text", 0.35))
    price_w = float(weights.get("price", 0.25))
    seller_w = float(weights.get("seller", 0.20))
    vision_w = float(weights.get("vision", 0.20))
    weight_sum = max(text_w + price_w + seller_w + vision_w, 0.01)

    raw_total = (
        text_score * text_w
        + price_score * price_w
        + seller_score * seller_w
        + vision_score * vision_w
    ) / weight_sum
    total_score = _clamp(raw_total - risk_penalty + (confidence_score - 50) * 0.1)

    if not reasons:
        reasons.append("商品基础信息符合监控条件")

    return ScoreBreakdown(
        total_score=round(total_score, 1),
        text_score=round(text_score, 1),
        price_score=round(price_score, 1),
        seller_score=round(seller_score, 1),
        vision_score=round(vision_score, 1),
        confidence_score=round(confidence_score, 1),
        risk_penalty=round(risk_penalty, 1),
        include_hits=include_hits,
        exclude_hits=exclude_hits,
        risk_tags=sorted(set(risk_tags)),
        reasons=reasons,
    )
