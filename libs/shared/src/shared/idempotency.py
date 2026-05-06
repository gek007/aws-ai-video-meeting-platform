from __future__ import annotations


class IdempotencyStore:
    def __init__(self) -> None:
        self._keys: set[str] = set()

    def seen(self, key: str) -> bool:
        return key in self._keys

    def remember(self, key: str) -> None:
        self._keys.add(key)

