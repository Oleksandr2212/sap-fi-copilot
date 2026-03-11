#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-/opt/sap-fi-copilot/backend}"
BACKUP_DIR="${BACKUP_DIR:-/opt/sap-fi-copilot/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
SERVICE_NAME="${SERVICE_NAME:-sap-fi-copilot}"
TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p "${BACKUP_DIR}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

if [[ ! -d "${APP_DIR}" ]]; then
  echo "ERROR: APP_DIR not found: ${APP_DIR}"
  exit 1
fi

cp -a "${APP_DIR}" "${TMP_DIR}/backend"

if [[ -r /etc/sap-fi-copilot.env ]]; then
  cp /etc/sap-fi-copilot.env "${TMP_DIR}/sap-fi-copilot.env"
fi

if [[ -r "/etc/systemd/system/${SERVICE_NAME}.service" ]]; then
  cp "/etc/systemd/system/${SERVICE_NAME}.service" "${TMP_DIR}/${SERVICE_NAME}.service"
fi

tar -czf "${BACKUP_DIR}/sap_fi_backup_${TS}.tar.gz" -C "${TMP_DIR}" .
find "${BACKUP_DIR}" -type f -name 'sap_fi_backup_*.tar.gz' -mtime +"${KEEP_DAYS}" -delete

echo "Backup created: ${BACKUP_DIR}/sap_fi_backup_${TS}.tar.gz"
