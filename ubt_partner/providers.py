from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class ProviderConfig:
    name: str
    endpoint: str
    api_key: str
    model: str


class ProviderRegistry:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def list_all(self) -> list[ProviderConfig]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [ProviderConfig(**item) for item in data]

    def save_all(self, providers: list[ProviderConfig]) -> None:
        payload = [asdict(p) for p in providers]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert(self, provider: ProviderConfig) -> None:
        providers = self.list_all()
        kept = [p for p in providers if p.name != provider.name]
        kept.append(provider)
        self.save_all(kept)

    def remove(self, name: str) -> None:
        providers = [p for p in self.list_all() if p.name != name]
        self.save_all(providers)


def call_provider(
    endpoint: str,
    api_key: str,
    model: str,
    prompt: str,
    timeout_sec: int = 30,
) -> str:
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests 패키지가 필요합니다: pip install requests") from exc

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout_sec)
    response.raise_for_status()

    data = response.json()
    if "choices" in data and data["choices"]:
        return data["choices"][0].get("message", {}).get("content", "")
    return json.dumps(data, ensure_ascii=False)
