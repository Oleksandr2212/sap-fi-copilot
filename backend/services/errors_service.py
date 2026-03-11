from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_ERROR_CODE_PATTERN = re.compile(r"\b([A-Z]\d)\s?(\d{3})\b", re.IGNORECASE)


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


class ErrorsService:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._errors: list[dict[str, Any]] = []
        self.reload()

    def reload(self) -> None:
        self._errors = _load_json(self._file_path)

    def find(self, message: str) -> dict[str, Any] | None:
        query = message.strip()
        if not query:
            return None

        query_lower = query.lower()
        normalized_query = _normalize(query)
        extracted_code = self.extract_code(query)

        for error in self._errors:
            code = str(error.get("code", "")).strip()
            title = str(error.get("title", "")).strip()
            normalized_code = _normalize(code)

            if extracted_code and normalized_code == extracted_code:
                return error

            if normalized_code and normalized_code in normalized_query:
                return error

            if title and title.lower() in query_lower:
                return error

        return None

    def total(self) -> int:
        return len(self._errors)

    @staticmethod
    def extract_code(message: str) -> str | None:
        match = _ERROR_CODE_PATTERN.search(message.upper())
        if not match:
            return None
        return f"{match.group(1)}{match.group(2)}"
