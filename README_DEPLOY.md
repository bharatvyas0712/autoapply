# AutoJobApply Azure VM Deployment Guide

This repository contains everything needed to securely deploy AutoJobApply on an Azure Linux VM.

## 1. Prerequisites (On your Azure Linux VM)
1. **Docker & Docker Compose**: Ensure Docker is installed on your Linux VM.
2. **Git**: Clone this repository to your VM.
3. **Azure NSG**: Open Ports 80 (HTTP) and 443 (HTTPS) in your Azure VM's Network Security Group.

## 2. Environment Setup
Rename the provided production template to `.env`:
```bash
cp .env.production .env
```
Open `.env` and change `JWT_SECRET` and `DB_PASSWORD` to secure strings.

## 3. Deploy
Run the deployment script:
```bash
./deploy.sh
```

### What `deploy.sh` does:
- Builds Docker images without using cache.
- Starts `mysql`, `backend`, `automation`, and `nginx` containers.
- Installs Playwright Chromium if it's missing in the automation container.
- Verifies endpoints `/`, `/api/health`, `/api/auth/login`, and `/automation/health`.
- Validates the MySQL container health status.

## 4. Backups and Restores
- **Backup**: Run `./backup.sh` to take a full MySQL snapshot. It will be stored in the `/backups` directory.
- **Restore**: Run `./restore.sh backups/db_backup_<timestamp>.sql` to restore a previous backup.

## 5. Security & Idempotency
- **Idempotent**: Running `./deploy.sh` multiple times will not break anything or delete your database. It simply restarts containers with any new code changes.
- **Data Persistence**: The MySQL database is safely stored in a Docker named volume (`mysql_data`), meaning your data survives container restarts and rebuilds.
- **Port Security**: The backend (`3000`) and automation (`5001`) services are currently exposed for verification, but you should eventually close them in `docker-compose.yml` and only expose Port `80` via Nginx.
