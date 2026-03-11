# VM Deploy + Backup + Cleanup

## 1) One-time VM setup

### Required packages
```bash
sudo apt update
sudo apt install -y python3-venv python3-pip rsync curl
```

### Allow GitHub deploy to restart service (passwordless sudo for limited commands)
Replace `YOUR_VM_USER` with your Linux user (e.g. `o_kurtyak`):

```bash
sudo tee /etc/sudoers.d/sap-fi-copilot-deploy > /dev/null <<'EOF'
YOUR_VM_USER ALL=(ALL) NOPASSWD:/bin/systemctl daemon-reload,/bin/systemctl restart sap-fi-copilot,/bin/systemctl status sap-fi-copilot,/usr/bin/systemctl daemon-reload,/usr/bin/systemctl restart sap-fi-copilot,/usr/bin/systemctl status sap-fi-copilot,/usr/bin/journalctl -u sap-fi-copilot *
EOF
sudo chmod 440 /etc/sudoers.d/sap-fi-copilot-deploy
```

## 2) GitHub Actions secrets
In GitHub repo settings, add these secrets:
- `VM_HOST` (example: `34.158.225.101`)
- `VM_USER` (example: `o_kurtyak`)
- `VM_SSH_KEY` (private SSH key content)

Workflow file: `.github/workflows/deploy-vm.yml`

## 3) Manual deploy (same logic as workflow)
```bash
cd /opt/sap-fi-copilot/backend
chmod +x deploy/vm/*.sh
./deploy/vm/deploy_vm.sh /opt/sap-fi-copilot/backend
```

## 4) Backup
Creates archive in `/opt/sap-fi-copilot/backups` and removes old backups.

```bash
cd /opt/sap-fi-copilot/backend
./deploy/vm/backup_backend.sh /opt/sap-fi-copilot/backend
```

Optional daily backup at 03:20:
```bash
(crontab -l 2>/dev/null; echo "20 3 * * * /opt/sap-fi-copilot/backend/deploy/vm/backup_backend.sh /opt/sap-fi-copilot/backend >> /var/log/sap-fi-backup.log 2>&1") | crontab -
```

## 5) Cleanup
Removes macOS metadata files (`.DS_Store`, `._*`) and fixes malformed names like `touch transactions.json`.

```bash
cd /opt/sap-fi-copilot/backend
./deploy/vm/cleanup_backend.sh /opt/sap-fi-copilot/backend
```

Optional daily cleanup at 03:40:
```bash
(crontab -l 2>/dev/null; echo "40 3 * * * /opt/sap-fi-copilot/backend/deploy/vm/cleanup_backend.sh /opt/sap-fi-copilot/backend >> /var/log/sap-fi-cleanup.log 2>&1") | crontab -
```

## 6) Health checks
```bash
curl -sS http://127.0.0.1:8000/telegram/health
sudo systemctl status sap-fi-copilot --no-pager
sudo journalctl -u sap-fi-copilot -n 100 --no-pager
```
