#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="${1:-}"
APP_DIR="${APP_DIR:-/opt/sap-fi-copilot/backend}"
SERVICE_NAME="${SERVICE_NAME:-sap-fi-copilot}"
BACKUP_DIR="${BACKUP_DIR:-/opt/sap-fi-copilot/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"

if [[ -z "${SRC_DIR}" ]]; then
  echo "Usage: $0 <source_backend_dir>"
  exit 1
fi

if [[ ! -f "${SRC_DIR}/requirements.txt" ]]; then
  echo "ERROR: ${SRC_DIR} does not look like backend dir (requirements.txt missing)"
  exit 1
fi

TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p "${BACKUP_DIR}"

if [[ -d "${APP_DIR}" ]]; then
  tar -czf "${BACKUP_DIR}/backend_predeploy_${TS}.tar.gz" -C "$(dirname "${APP_DIR}")" "$(basename "${APP_DIR}")"
fi

mkdir -p "${APP_DIR}"

rsync -a --delete \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.DS_Store' \
  --exclude '._*' \
  "${SRC_DIR}/" "${APP_DIR}/"

if [[ -x "${APP_DIR}/deploy/vm/cleanup_backend.sh" ]]; then
  "${APP_DIR}/deploy/vm/cleanup_backend.sh" "${APP_DIR}" || true
fi

python3 -m venv "${APP_DIR}/.venv"
source "${APP_DIR}/.venv/bin/activate"
pip install --upgrade pip >/dev/null
pip install -r "${APP_DIR}/requirements.txt"

if [[ -f /etc/systemd/system/${SERVICE_NAME}.service ]]; then
  sudo systemctl daemon-reload
  sudo systemctl restart "${SERVICE_NAME}"
  sleep 2

  if ! curl -fsS http://127.0.0.1:8000/telegram/health >/dev/null; then
    echo "ERROR: health check failed"
    sudo systemctl status "${SERVICE_NAME}" --no-pager || true
    sudo journalctl -u "${SERVICE_NAME}" -n 100 --no-pager || true
    exit 1
  fi

  echo "Deploy OK: service ${SERVICE_NAME} is healthy"
else
  echo "WARNING: /etc/systemd/system/${SERVICE_NAME}.service not found"
  echo "Backend was updated, but service restart was skipped"
fi

find "${BACKUP_DIR}" -type f -name 'backend_predeploy_*.tar.gz' -mtime +"${KEEP_DAYS}" -delete
