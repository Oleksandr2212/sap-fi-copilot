from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal
from urllib import error as urllib_error
from urllib import request as urllib_request

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from services.errors_service import ErrorsService
from services.guides_service import GuidesService
from services.transactions_service import TransactionsService

BASE_DIR = Path(__file__).parent

errors_service = ErrorsService(BASE_DIR / "errors.json")
transactions_service = TransactionsService(
    [
        BASE_DIR / "transactions.json",
        BASE_DIR / "open_data" / "transactions_open.json",
    ]
)
guides_service = GuidesService(BASE_DIR / "guides.json")

app = FastAPI(title="SAP FI Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AskMode = Literal["general", "error", "transaction", "guide"]


class AskRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    mode: AskMode = "general"

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("Поле message не може бути порожнім")
        return clean


class AskResponse(BaseModel):
    type: str
    title: str
    reason: str
    checks: list[str]
    solution: list[str]
    tcode: str | None
    source: str | None = None


def _clean_list(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = str(value).strip()
        if not text:
            continue

        marker = text.lower()
        if marker in seen:
            continue

        seen.add(marker)
        cleaned.append(text)

    return cleaned


def _build_error_response(error: dict) -> AskResponse:
    source = str(error.get("source", "")).strip() or None
    code = str(error.get("code", "")).strip()
    title = str(error.get("title", "SAP помилка")).strip()
    base_reason = str(error.get("reason", "")).strip()
    tcode = error.get("tcode")

    reason = "\n\n".join(
        [
            base_reason or "Система повернула помилку під час обробки FI документа.",
            "Що це означає: помилка вказує на невідповідність даних документа або налаштувань FI.",
            "Практичний вплив: документ не буде проведений, доки не усунути першопричину.",
            f"Де перевіряти: почніть з транзакції {tcode}." if tcode else "Де перевіряти: почніть з документа, який викликав помилку.",
        ]
    )

    checks = _clean_list(
        [
            *[str(item) for item in error.get("checks", [])],
            "Перевірте company code, дату документа і відкритий період (OB52).",
            "Перевірте обов'язкові поля: МВЗ/внутрішнє замовлення/податок/терміни оплати.",
            "Перевірте master data контрагента і статус блокувань.",
            "Перевірте валюту документа і наявність курсу обміну (OB08).",
        ]
    )

    solution = _clean_list(
        [
            "Запустіть симуляцію документа і визначте рядок, який викликає помилку.",
            *[str(item) for item in error.get("solution", [])],
            "Виправте дані документа або налаштування, які спричинили помилку.",
            "Проведіть документ повторно і перевірте результат у FB03/FBL*.",
            "Зафіксуйте причину і виправлення для команди підтримки/аудиту.",
        ]
    )

    return AskResponse(
        type="error_explainer",
        title=f"{code} - {title}" if code else title,
        reason=reason,
        checks=checks,
        solution=solution,
        tcode=tcode,
        source=source,
    )


def _build_transaction_response(transaction: dict) -> AskResponse:
    module = str(transaction.get("module", "")).strip()
    source = str(transaction.get("source", "")).strip() or None
    tcode = str(transaction.get("tcode", "")).strip() or None
    name = str(transaction.get("name", "SAP транзакція")).strip()
    description = str(transaction.get("description", "")).strip()

    reason = "\n\n".join(
        [
            description or "Транзакція використовується для виконання стандартної FI операції.",
            f"Функціональна зона: {module}." if module else "Функціональна зона: SAP FI.",
            "Коли застосовувати: коли потрібно виконати цю операцію вручну або перевірити її результат.",
            "Практична порада: спочатку виконуйте операцію на тестовому середовищі/тестових даних.",
        ]
    )

    checks = _clean_list(
        [
            f"Модуль: {module}" if module else "Модуль: SAP FI",
            "Перевірте, що період відкритий у OB52.",
            "Переконайтесь у наявності авторизації на цю транзакцію.",
            "Перевірте master data (клієнт/постачальник/GL-рахунок).",
            "Перевірте валюту, податкові коди і company code.",
        ]
    )

    solution = _clean_list(
        [
            "Підготуйте вхідні дані документа перед запуском транзакції.",
            *[str(item) for item in transaction.get("steps", [])],
            "Перед постингом використайте перевірку/симуляцію, якщо доступно.",
            "Після виконання перевірте створений документ у FB03 або відповідному звіті.",
            "Якщо є помилка, зафіксуйте код і повторіть операцію після виправлення даних.",
        ]
    )

    return AskResponse(
        type="transaction_help",
        title=f"{tcode} - {name}" if tcode else name,
        reason=reason,
        checks=checks,
        solution=solution,
        tcode=tcode,
        source=source,
    )


def _build_guide_response(guide: dict) -> AskResponse:
    source = str(guide.get("source", "")).strip() or None
    tcode = guide.get("tcode")
    title = str(guide.get("title", "How-to інструкція")).strip()
    description = str(guide.get("description", "")).strip()

    reason = "\n\n".join(
        [
            description or "Покрокова інструкція для SAP FI процесу.",
            "Сценарій: інструкція орієнтована на виконання операції без пропуску критичних перевірок.",
            "Очікуваний результат: документ або операція повинні бути виконані без FI помилок.",
        ]
    )

    checks = _clean_list(
        [
            *[str(item) for item in guide.get("checks", [])],
            "Підготуйте вхідні дані: company code, контрагент, суми, податок, валюта.",
            "Переконайтесь, що період відкрито і довідники актуальні.",
            "За потреби погодьте операцію з відповідальним бухгалтером.",
        ]
    )

    solution = _clean_list(
        [
            "Виконайте кроки нижче послідовно без пропусків.",
            *[str(item) for item in guide.get("steps", [])],
            "Після завершення перевірте результат у звіті або перегляді документа.",
            "Якщо виникла помилка, поверніться до блоку перевірок і повторіть процес.",
        ]
    )

    return AskResponse(
        type="how_to_guide",
        title=title,
        reason=reason,
        checks=checks,
        solution=solution,
        tcode=tcode,
        source=source,
    )


def _build_fallback_response(mode: AskMode) -> AskResponse:
    reasons_by_mode = {
        "general": "Поки що я не знайшов точну відповідь у базі знань.",
        "error": "Не знайшов цю SAP помилку у довіднику помилок.",
        "transaction": "Не знайшов цю транзакцію у поточній базі T-codes.",
        "guide": "Не знайшов релевантну how-to інструкцію для цього запиту.",
    }

    checks_by_mode = {
        "general": [
            "Спробуйте короткий запит: F5 808, FB60, F110.",
            "Для помилки використовуйте формат: літера+цифра та номер (наприклад F5 263).",
            "Для транзакції використовуйте точний T-code (наприклад FBL1N).",
        ],
        "error": [
            "Введіть код помилки у форматі: F5 808.",
            "Перевірте пробіл у коді (допускається F5808 або F5 808).",
            "Спробуйте повідомлення без зайвого тексту.",
        ],
        "transaction": [
            "Введіть точний T-code: FB60, F-47, OB08, AFAB.",
            "Спробуйте альтернативне написання з дефісом/крапкою: F-05, F.13.",
            "Якщо не знаходить, напишіть призначення транзакції словами.",
        ],
        "guide": [
            "Опишіть процес простими словами: як провести рахунок постачальника.",
            "Додайте ключову дію: оплата, очищення, відкриття періоду, платежі.",
            "За потреби вкажіть T-code для контексту.",
        ],
    }

    solution_by_mode = {
        "general": [
            "Оберіть зліва конкретний режим: помилки, транзакції або how-to.",
            "Надішліть один приклад із швидких кнопок.",
            "Після отримання відповіді уточніть company code/період/валюту.",
        ],
        "error": [
            "Скопіюйте точний код помилки з SAP статус-рядка.",
            "Надішліть код окремим повідомленням.",
            "Отримайте перевірки і виконайте їх по черзі.",
        ],
        "transaction": [
            "Надішліть точний T-code окремим повідомленням.",
            "Виконайте рекомендовані кроки з блоку 'Що зробити'.",
            "Перевірте результат у пов'язаному звіті/документі.",
        ],
        "guide": [
            "Опишіть задачу у форматі: що потрібно зробити + для кого.",
            "Отримайте покроковий сценарій та виконайте його послідовно.",
            "Поверніться з помилкою, якщо якийсь крок не спрацював.",
        ],
    }

    return AskResponse(
        type="fallback",
        title="Відповідь не знайдено",
        reason=reasons_by_mode.get(mode, reasons_by_mode["general"]),
        checks=checks_by_mode.get(mode, checks_by_mode["general"]),
        solution=solution_by_mode.get(mode, solution_by_mode["general"]),
        tcode=None,
        source=None,
    )


def _run_ask_pipeline(message: str, mode: AskMode) -> AskResponse:
    if mode == "error":
        error_match = errors_service.find(message)
        return _build_error_response(error_match) if error_match else _build_fallback_response(mode)

    if mode == "transaction":
        transaction_match = transactions_service.find(message)
        return _build_transaction_response(transaction_match) if transaction_match else _build_fallback_response(mode)

    if mode == "guide":
        guide_match = guides_service.find(message)
        return _build_guide_response(guide_match) if guide_match else _build_fallback_response(mode)

    error_match = errors_service.find(message)
    if error_match:
        return _build_error_response(error_match)

    transaction_match = transactions_service.find(message)
    if transaction_match:
        return _build_transaction_response(transaction_match)

    guide_match = guides_service.find(message)
    if guide_match:
        return _build_guide_response(guide_match)

    return _build_fallback_response("general")


def _knowledge_stats_payload() -> dict:
    return {
        "transactions_total": transactions_service.total(),
        "transactions_sources": transactions_service.stats(),
        "errors_total": errors_service.total(),
        "guides_total": guides_service.total(),
    }


def _telegram_env() -> tuple[str, str, str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    secret_token = os.getenv("TELEGRAM_SECRET_TOKEN", "").strip()
    return token, webhook_secret, secret_token


def _telegram_api_post(method: str, payload: dict) -> dict:
    token, _, _ = _telegram_env()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не налаштовано")

    url = f"https://api.telegram.org/bot{token}/{method}"
    body = json.dumps(payload).encode("utf-8")
    request = urllib_request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib_request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except urllib_error.HTTPError as error:
        details = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Telegram API HTTP {error.code}: {details}") from error
    except urllib_error.URLError as error:
        raise RuntimeError(f"Telegram API недоступний: {error}") from error


def _telegram_send_message(chat_id: int, text: str) -> None:
    _telegram_api_post(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text[:4000],
            "disable_web_page_preview": True,
        },
    )


def _telegram_parse_mode(text: str) -> tuple[AskMode, str]:
    normalized = text.strip()

    mapping: list[tuple[str, AskMode]] = [
        ("/error", "error"),
        ("/transaction", "transaction"),
        ("/tcode", "transaction"),
        ("/guide", "guide"),
        ("/ask", "general"),
    ]

    lowered = normalized.lower()
    for command, mode in mapping:
        if lowered.startswith(command):
            query = normalized[len(command):].strip()
            return mode, query

    return "general", normalized


def _telegram_help_text() -> str:
    return "\n".join(
        [
            "SAP FI Copilot (Telegram) готовий.",
            "",
            "Основні команди:",
            "/ask FB60 - загальний режим",
            "/error F5 808 - пояснення помилки",
            "/transaction F110 - довідка по транзакції",
            "/guide як запустити автоматичні платежі - покроковий гайд",
            "",
            "Додаткові команди:",
            "/find оплата постачальнику - знайти найкращу відповідь",
            "/source FB60 - показати джерело знань",
            "/stats - статистика бази знань",
            "/modes - режими і приклади",
            "/health - стан Telegram інтеграції",
            "",
            "Можна також писати без команди, тоді спрацює загальний режим.",
        ]
    )


def _telegram_modes_text() -> str:
    return "\n".join(
        [
            "Режими SAP FI Copilot:",
            "",
            "1) Загальний",
            "Приклад: FB70 або як провести вхідний платіж",
            "",
            "2) Помилки",
            "Приклад: /error F5 808",
            "",
            "3) Транзакції",
            "Приклад: /transaction F-28",
            "",
            "4) How-to",
            "Приклад: /guide як закрити відкриті позиції клієнта",
        ]
    )


def _telegram_stats_text() -> str:
    stats = _knowledge_stats_payload()
    source_lines = [
        f"• {Path(path).name}: {count}"
        for path, count in stats["transactions_sources"].items()
    ]
    return "\n".join(
        [
            "Статистика бази знань:",
            f"• Транзакції: {stats['transactions_total']}",
            f"• Помилки: {stats['errors_total']}",
            f"• Гайди: {stats['guides_total']}",
            "",
            "Джерела транзакцій:",
            *source_lines,
        ]
    )


def _telegram_source_text(query: str) -> str:
    clean_query = query.strip()
    if not clean_query:
        return "Використання: /source <F5 808|FB60|тема гайду>"

    error = errors_service.find(clean_query)
    if error:
        return "\n".join(
            [
                f"Тип: SAP помилка",
                f"Код: {error.get('code', '-')}",
                f"Назва: {error.get('title', '-')}",
                f"T-code: {error.get('tcode', '-')}",
                f"Джерело: {error.get('source', 'internal')}",
            ]
        )

    transaction = transactions_service.find(clean_query)
    if transaction:
        return "\n".join(
            [
                f"Тип: SAP транзакція",
                f"T-code: {transaction.get('tcode', '-')}",
                f"Назва: {transaction.get('name', '-')}",
                f"Модуль: {transaction.get('module', '-')}",
                f"Джерело: {transaction.get('source', 'internal')}",
            ]
        )

    guide = guides_service.find(clean_query)
    if guide:
        return "\n".join(
            [
                f"Тип: How-to гайд",
                f"Назва: {guide.get('title', '-')}",
                f"T-code: {guide.get('tcode', '-')}",
                f"Джерело: {guide.get('source', 'internal')}",
            ]
        )

    return "Джерело не знайдено. Спробуйте точний код помилки або T-code."


def _telegram_format_answer(answer: AskResponse) -> str:
    lines: list[str] = [answer.title, "", answer.reason]

    if answer.checks:
        lines.append("")
        lines.append("Що перевірити:")
        lines.extend([f"• {item}" for item in answer.checks])

    if answer.solution:
        lines.append("")
        lines.append("Що зробити:")
        lines.extend([f"• {item}" for item in answer.solution])

    if answer.tcode:
        lines.append("")
        lines.append(f"T-code: {answer.tcode}")

    if answer.source:
        lines.append(f"Джерело: {answer.source}")

    text = "\n".join(lines).strip()
    if len(text) > 4000:
        return text[:3990].rstrip() + "..."
    return text


def _handle_telegram_update(update: dict) -> bool:
    message = update.get("message") or update.get("edited_message")
    if not isinstance(message, dict):
        return False

    chat = message.get("chat")
    if not isinstance(chat, dict):
        return False

    chat_id = chat.get("id")
    text = str(message.get("text", "")).strip()

    if not isinstance(chat_id, int):
        return False

    if not text:
        _telegram_send_message(chat_id, "Підтримуються лише текстові повідомлення.")
        return True

    lowered = text.lower()

    if lowered in {"/start", "/help"}:
        _telegram_send_message(chat_id, _telegram_help_text())
        return True

    if lowered.startswith("/stats"):
        _telegram_send_message(chat_id, _telegram_stats_text())
        return True

    if lowered.startswith("/modes"):
        _telegram_send_message(chat_id, _telegram_modes_text())
        return True

    if lowered.startswith("/health"):
        token, webhook_secret, secret_token = _telegram_env()
        _telegram_send_message(
            chat_id,
            "\n".join(
                [
                    "Стан Telegram інтеграції:",
                    f"• BOT_TOKEN: {'ok' if token else 'missing'}",
                    f"• WEBHOOK_SECRET: {'ok' if webhook_secret else 'missing'}",
                    f"• SECRET_TOKEN: {'ok' if secret_token else 'missing'}",
                ]
            ),
        )
        return True

    if lowered.startswith("/source"):
        query = text[len("/source") :].strip()
        _telegram_send_message(chat_id, _telegram_source_text(query))
        return True

    if lowered.startswith("/find"):
        query = text[len("/find") :].strip()
        if not query:
            _telegram_send_message(chat_id, "Використання: /find <помилка|tcode|процес>")
            return True

        answer = _run_ask_pipeline(query, "general")
        _telegram_send_message(chat_id, _telegram_format_answer(answer))
        return True

    mode, query = _telegram_parse_mode(text)
    if not query:
        defaults: dict[AskMode, str] = {
            "general": "FB60",
            "error": "F5 808",
            "transaction": "F110",
            "guide": "як запустити автоматичні платежі",
        }
        query = defaults[mode]

    answer = _run_ask_pipeline(query, mode)
    _telegram_send_message(chat_id, _telegram_format_answer(answer))
    return True


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "SAP FI Copilot backend працює"}


@app.get("/knowledge/stats")
def knowledge_stats() -> dict:
    return _knowledge_stats_payload()


@app.get("/telegram/health")
def telegram_health() -> dict[str, bool]:
    token, webhook_secret, _ = _telegram_env()
    return {
        "telegram_token_configured": bool(token),
        "telegram_webhook_secret_configured": bool(webhook_secret),
    }


@app.post("/telegram/webhook/{webhook_secret}")
async def telegram_webhook(webhook_secret: str, request: Request) -> dict[str, bool | str]:
    token, expected_secret, secret_token = _telegram_env()

    if not token or not expected_secret:
        raise HTTPException(status_code=503, detail="Telegram bot не налаштований")

    if webhook_secret != expected_secret:
        raise HTTPException(status_code=403, detail="Webhook secret невалідний")

    if secret_token:
        header = request.headers.get("x-telegram-bot-api-secret-token", "")
        if header != secret_token:
            raise HTTPException(status_code=403, detail="Telegram secret token невалідний")

    payload = await request.json()
    if not isinstance(payload, dict):
        return {"ok": True, "handled": False, "message": "Invalid payload"}

    try:
        handled = _handle_telegram_update(payload)
        return {"ok": True, "handled": handled}
    except Exception:
        return {
            "ok": True,
            "handled": False,
            "message": "Telegram update отримано, але обробка завершилась з помилкою",
        }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        return _run_ask_pipeline(request.message, request.mode)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Не вдалося обробити запит. Спробуйте ще раз.",
        ) from error
