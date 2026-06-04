from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class GoofishItem:
    item_id: str
    title: str
    price: float | None = None
    location: str = ""
    seller_name: str = ""
    image_url: str = ""
    item_link: str = ""
    chat_link: str = ""
    description: str = ""
    keyword: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
