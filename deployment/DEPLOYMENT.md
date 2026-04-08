# Deployment Guide

This document describes how to deploy the Randebu Trading Bot application to a production server.

## Prerequisites

- Debian server with 8GB RAM, 4 cores
- Python 3.10+
- Node.js 18+
- Nginx
- SSL certificate (Let's Encrypt)
- SSH access to server

## Server Structure

```
/var/www/
  └── bot/
      ├── backend/          # Backend application (FastAPI)
      ├── frontend/         # Frontend static files (SvelteKit build)
      └── data/             # SQLite database and app data
```

## Step-by-Step Deployment

### 1. Clone Repository

```bash
ssh user@your-server
sudo mkdir -p /var/www/bot
sudo chown -R $USER:$USER /var/www/bot
cd /var/www/bot
git clone https://git.example.com/shoko/randebu.git .
```

### 2. Setup Backend

```bash
cd /var/www/bot/src/backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

mkdir -p /var/www/bot/data
```

### 3. Configure Environment

Copy and configure the environment file:

```bash
cp src/backend/.env.example /var/www/bot/data/.env
nano /var/www/bot/data/.env
```

Update these values:
- `SECRET_KEY` - Generate a secure key
- `DATABASE_URL` - Update path to `/var/www/bot/data/app.db`
- `MINIMAX_API_KEY` - Your API key
- `AVE_API_KEY` - Your API key

### 4. Build Frontend

```bash
cd /var/www/bot/src/frontend
npm install
npm run build

# Move build to expected location
mkdir -p /var/www/bot/frontend
cp -r build/* /var/www/bot/frontend/
```

### 5. Configure Nginx

Copy the nginx template and modify as needed:

```bash
sudo cp /var/www/bot/deployment/scripts/nginx-template.conf /etc/nginx/sites-available/bot.yourdomain.com
sudo nano /etc/nginx/sites-available/bot.yourdomain.com
```

Update `bot.yourdomain.com` with your actual domain.

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/bot.yourdomain.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Setup SSL Certificate

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d bot.yourdomain.com
```

### 7. Configure Systemd Service

Copy and configure the systemd service:

```bash
sudo cp /var/www/bot/deployment/scripts/systemd-template.service /etc/systemd/system/ave-backend.service
sudo nano /etc/systemd/system/ave-backend.service
```

Update `your-user` and `/var/www/bot` paths as needed.

### 8. Start Backend Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable ave-backend
sudo systemctl start ave-backend
sudo systemctl status ave-backend
```

### 9. Configure Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 10. Verify Deployment

1. Visit `https://bot.yourdomain.com` - should show frontend
2. Visit `https://bot.yourdomain.com/api/...` - should hit backend API
3. Check backend logs: `sudo journalctl -u ave-backend -f`

## Project Structure

```
/var/www/bot/
├── deployment/              # Deployment scripts and templates
│   ├── DEPLOYMENT.md       # This file
│   └── scripts/
│       ├── nginx-template.conf
│       ├── systemd-template.service
│       └── deploy.sh       # Automated deployment script
├── src/
│   ├── backend/            # FastAPI application
│   │   ├── app/
│   │   │   ├── api/       # API routes
│   │   │   ├── core/      # Core functionality
│   │   │   ├── db/        # Database models
│   │   │   └── services/  # Business logic
│   │   ├── run.py
│   │   └── requirements.txt
│   └── frontend/           # SvelteKit application
│       ├── src/
│       └── package.json
├── data/                   # Runtime data (gitignored)
│   ├── app.db             # SQLite database
│   └── .env               # Environment variables
└── frontend/              # Built frontend static files
```

## Troubleshooting

### Backend won't start

Check logs:
```bash
sudo journalctl -u ave-backend -n 100
```

Common issues:
- Missing environment variables - check `.env` file
- Port 8000 already in use - check configuration
- Database path incorrect - verify paths

### Nginx errors

Test configuration:
```bash
sudo nginx -t
```

Check error logs:
```bash
sudo tail -f /var/log/nginx/error.log
```

### SSL certificate issues

Renew certificate:
```bash
sudo certbot renew
```

Check certificate status:
```bash
sudo certbot certificates
```

## Useful Commands

| Action | Command |
|--------|---------|
| Restart backend | `sudo systemctl restart ave-backend` |
| View backend logs | `sudo journalctl -u ave-backend -f` |
| Check nginx status | `sudo systemctl status nginx` |
| Reload nginx | `sudo systemctl reload nginx` |
| Check port 8000 | `curl http://localhost:8000/health` |

## Rolling Updates

To update the application:

```bash
cd /var/www/bot
git pull
cd src/backend && source venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart ave-backend
```

For frontend updates, rebuild and copy static files to `/var/www/bot/frontend`.