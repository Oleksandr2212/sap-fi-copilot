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


class GuidesService:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._guides: list[dict[str, Any]] = []
        self.reload()

    def reload(self) -> None:
        self._guides = _load_json(self._file_path)

    def find(self, message: str) -> dict[str, Any] | None:
        query = message.strip()
        if not query:
            return None

        query_lower = query.lower()
        normalized_query = _normalize(query)
        query_words = [word for word in re.findall(r"[\w-]+", query_lower) if len(word) >= 4]

        for guide in self._guides:
            title = str(guide.get("title", "")).strip()
            description = str(guide.get("description", "")).strip()
            tcode = str(guide.get("tcode", "")).strip()
            keywords = [str(keyword).strip() for keyword in guide.get("keywords", [])]

            haystack = " ".join([title, description, *keywords]).lower()

            if tcode and _normalize(tcode) in normalized_query:
                return guide

            if title and title.lower() in query_lower:
                return guide

            if description and description.lower() in query_lower:
                return guide

            if query_lower in haystack:
                return guide

            if query_words:
                matched_words = sum(1 for word in query_words if word in haystack)
                if matched_words >= min(2, len(query_words)):
                    return guide

            for keyword in keywords:
                keyword_text = keyword.lower()
                if keyword_text and keyword_text in query_lower:
                    return guide

        return None

    def total(self) -> int:
        return len(self._guides)
