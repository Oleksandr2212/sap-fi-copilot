#!/usr/bin/env bash
set -euo pipefail

: "${TELEGRAM_BOT_TOKEN:?Set TELEGRAM_BOT_TOKEN}"
: "${SERVICE_URL:?Set SERVICE_URL (Cloud Run URL)}"
: "${TELEGRAM_WEBHOOK_SECRET:?Set TELEGRAM_WEBHOOK_SECRET}"

WEBHOOK_URL="${SERVICE_URL%/}/telegram/webhook/${TELEGRAM_WEBHOOK_SECRET}"

if [[ -n "${TELEGRAM_SECRET_TOKEN:-}" ]]; then
  curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
    -H 'Content-Type: application/json' \
    -d "{\"url\":\"${WEBHOOK_URL}\",\"secret_token\":\"${TELEGRAM_SECRET_TOKEN}\"}"
else
  curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
    -H 'Content-Type: application/json' \
    -d "{\"url\":\"${WEBHOOK_URL}\"}"
fi

echo
echo "Webhook set: ${WEBHOOK_URL}"
