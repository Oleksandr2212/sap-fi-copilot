from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value).upper()


def _load_json(file_path: Path) -> list[dict[str, Any]]:
    if not file_path.exists():
        return []

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    return [item for item in data if isinstance(item, dict)]


class TransactionsService:
    def __init__(self, file_paths: list[Path]) -> None:
        self._file_paths = file_paths
        self._transactions: list[dict[str, Any]] = []
        self._stats: dict[str, int] = {}
        self.reload()

    def reload(self) -> None:
        merged: list[dict[str, Any]] = []
        seen_tcodes: set[str] = set()
        stats: dict[str, int] = {}

        for file_path in self._file_paths:
            loaded = _load_json(file_path)
            accepted = 0

            for item in loaded:
                tcode = _normalize(str(item.get("tcode", "")).strip())
                if not tcode or tcode in seen_tcodes:
                    continue

                seen_tcodes.add(tcode)
                merged.append(item)
                accepted += 1

            stats[str(file_path)] = accepted

        self._transactions = merged
        self._stats = stats

    def find(self, message: str) -> dict[str, Any] | None:
        query = message.strip()
        if not query:
            return None

        query_lower = query.lower()
        normalized_query = _normalize(query)

        for transaction in self._transactions:
            tcode = str(transaction.get("tcode", "")).strip()
            name = str(transaction.get("name", "")).strip()
            description = str(transaction.get("description", "")).strip()
            normalized_tcode = _normalize(tcode)

            if normalized_tcode and normalized_tcode in normalized_query:
                return transaction

            if name and name.lower() in query_lower:
                return transaction

            if description and description.lower() in query_lower:
                return transaction

        return None

    def total(self) -> int:
        return len(self._transactions)

    def stats(self) -> dict[str, int]:
        return dict(self._stats)
