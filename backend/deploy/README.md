# Backend Deployment

## Option A: Google Cloud Run

### 1) Preconditions
- Google Cloud project with billing enabled
- APIs enabled:
  - Cloud Run API
  - Cloud Build API
  - Artifact Registry API
- Installed and authenticated `gcloud`
- Created Telegram bot via `@BotFather` and got token

### 2) Required env vars
- `PROJECT_ID`
- `REGION` (example: `europe-central2`)
- `SERVICE_NAME` (optional, default: `sap-fi-copilot-bot`)
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `TELEGRAM_SECRET_TOKEN` (optional but recommended)

### 3) Deploy
```bash
cd backend/deploy
chmod +x deploy_cloud_run.sh set_webhook.sh

export PROJECT_ID="your-gcp-project-id"
export REGION="europe-central2"
export SERVICE_NAME="sap-fi-copilot-bot"
export TELEGRAM_BOT_TOKEN="123456:ABC..."
export TELEGRAM_WEBHOOK_SECRET="your-unique-webhook-secret"
export TELEGRAM_SECRET_TOKEN="your-telegram-header-secret"

./deploy_cloud_run.sh
```

### 4) Validate
- Open `https://<cloud-run-url>/telegram/health`
- Send `/start` to your bot in Telegram
- Send test messages:
  - `/error F5 808`
  - `/transaction F110`
  - `/guide як запустити автоматичні платежі`
  - `/stats`

### 5) Update webhook only
```bash
cd backend/deploy
export TELEGRAM_BOT_TOKEN="..."
export SERVICE_URL="https://<cloud-run-url>"
export TELEGRAM_WEBHOOK_SECRET="..."
export TELEGRAM_SECRET_TOKEN="..." # optional
./set_webhook.sh
```

---

## Option B: VM + systemd + GitHub Actions (recommended for your current setup)
- Autodeploy workflow: `.github/workflows/deploy-vm.yml`
- VM scripts and setup: `backend/deploy/vm/README.md`
- Deploy script: `backend/deploy/vm/deploy_vm.sh`
- Backup script: `backend/deploy/vm/backup_backend.sh`
- Cleanup script: `backend/deploy/vm/cleanup_backend.sh`
