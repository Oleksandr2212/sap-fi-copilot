#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-/opt/sap-fi-copilot/backend}"

if [[ ! -d "${APP_DIR}" ]]; then
  echo "ERROR: APP_DIR not found: ${APP_DIR}"
  exit 1
fi

find "${APP_DIR}" -type f \( -name '.DS_Store' -o -name '._*' \) -delete
find "${APP_DIR}" -type d -name '__pycache__' -prune -exec rm -rf {} +

# Fix files accidentally named like: "touch transactions.json"
shopt -s nullglob
for bad_file in "${APP_DIR}"/touch\ *.json; do
  bad_name="$(basename "${bad_file}")"
  clean_name="${bad_name#touch }"
  clean_path="${APP_DIR}/${clean_name}"

  if [[ -f "${clean_path}" ]]; then
    rm -f "${bad_file}"
  else
    mv "${bad_file}" "${clean_path}"
  fi
done
shopt -u nullglob

echo "Cleanup completed for ${APP_DIR}"
