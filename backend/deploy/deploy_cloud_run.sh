#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID}"
: "${REGION:?Set REGION (example: europe-central2)}"
: "${SERVICE_NAME:=sap-fi-copilot-bot}"
: "${TELEGRAM_BOT_TOKEN:?Set TELEGRAM_BOT_TOKEN}"
: "${TELEGRAM_WEBHOOK_SECRET:?Set TELEGRAM_WEBHOOK_SECRET}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

ENV_VARS=(
  "TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}"
  "TELEGRAM_WEBHOOK_SECRET=${TELEGRAM_WEBHOOK_SECRET}"
)

if [[ -n "${TELEGRAM_SECRET_TOKEN:-}" ]]; then
  ENV_VARS+=("TELEGRAM_SECRET_TOKEN=${TELEGRAM_SECRET_TOKEN}")
fi

IFS=,
ENV_STRING="${ENV_VARS[*]}"
unset IFS

echo "[1/3] Deploying Cloud Run service ${SERVICE_NAME}..."
gcloud run deploy "${SERVICE_NAME}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --source "${BACKEND_DIR}" \
  --allow-unauthenticated \
  --set-env-vars "${ENV_STRING}"

echo "[2/3] Reading service URL..."
SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" --project "${PROJECT_ID}" --region "${REGION}" --format='value(status.url)')"
WEBHOOK_URL="${SERVICE_URL}/telegram/webhook/${TELEGRAM_WEBHOOK_SECRET}"

echo "[3/3] Configuring Telegram webhook..."
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
echo "Cloud Run URL: ${SERVICE_URL}"
echo "Webhook URL:   ${WEBHOOK_URL}"
echo "Health:        ${SERVICE_URL}/telegram/health"
echo "Knowledge:     ${SERVICE_URL}/knowledge/stats"
