from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _normalize_cookie(cookie: dict[str, Any]) -> dict[str, Any] | None:
    name = cookie.get("name")
    value = cookie.get("value")
    domain = cookie.get("domain") or cookie.get("host") or cookie.get("url")
    if not name or value is None or not domain:
        return None

    if isinstance(domain, str) and domain.startswith("http"):
        domain = ".goofish.com"
    if isinstance(domain, str) and "goofish" not in domain and "taobao" not in domain and "tmall" not in domain and "alicdn" not in domain:
        domain = ".goofish.com"

    normalized = {
        "name": str(name),
        "value": str(value),
        "domain": str(domain),
        "path": str(cookie.get("path") or "/"),
        "httpOnly": bool(cookie.get("httpOnly", cookie.get("http_only", False))),
        "secure": bool(cookie.get("secure", True)),
    }

    same_site = cookie.get("sameSite") or cookie.get("same_site")
    if same_site in {"Strict", "Lax", "None"}:
        normalized["sameSite"] = same_site

    expires = cookie.get("expires") or cookie.get("expirationDate")
    if isinstance(expires, (int, float)) and expires > 0:
        normalized["expires"] = float(expires)

    return normalized


def normalize_login_state(raw: Any) -> dict[str, Any]:
    cookies: list[dict[str, Any]] = []
    origins: list[dict[str, Any]] = []

    if isinstance(raw, list):
        source_cookies = raw
    elif isinstance(raw, dict):
        source_cookies = raw.get("cookies") or raw.get("cookie") or []
        origins = raw.get("origins") or raw.get("localStorage") or []
    else:
        source_cookies = []

    for item in source_cookies:
        if isinstance(item, dict):
            normalized = _normalize_cookie(item)
            if normalized:
                cookies.append(normalized)

    return {"cookies": cookies, "origins": origins if isinstance(origins, list) else []}


class AccountStore:
    def __init__(self, account_dir: str = "state/accounts"):
        self.account_dir = Path(account_dir)
        self.account_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, name: str) -> Path:
        safe = "".join(ch for ch in name if ch.isalnum() or ch in {"-", "_"}).strip() or "default"
        return self.account_dir / f"{safe}.json"

    def status_path_for(self, name: str) -> Path:
        safe = self.path_for(name).stem
        return self.account_dir / f"{safe}.status.json"

    def import_from_file(self, name: str, source_file: str) -> Path:
        raw = json.loads(Path(source_file).read_text(encoding="utf-8"))
        state = normalize_login_state(raw)
        target = self.path_for(name)
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        self.mark_status(name, "ok", "imported")
        return target

    def load(self, name: str) -> dict[str, Any] | None:
        path = self.path_for(name)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_accounts(self) -> list[str]:
        return sorted(p.stem for p in self.account_dir.glob("*.json") if not p.name.endswith(".status.json"))

    def mark_status(self, name: str, status: str, reason: str = "") -> None:
        import datetime as _dt

        payload = {
            "name": name,
            "status": status,
            "reason": reason,
            "updated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        }
        self.status_path_for(name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_status(self, name: str) -> dict[str, Any]:
        path = self.status_path_for(name)
        if not path.exists():
            return {"name": name, "status": "unknown", "reason": "", "updated_at": ""}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"name": name, "status": "unknown", "reason": "状态文件读取失败", "updated_at": ""}

    def list_accounts_with_status(self) -> list[dict[str, Any]]:
        return [self.load_status(name) | {"name": name} for name in self.list_accounts()]
