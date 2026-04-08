#!/bin/bash
set -e

DEPLOY_DIR="/var/www/bot"
DOMAIN="bot.yourdomain.com"
GIT_REPO="https://git.example.com/shoko/randebu.git"
BRANCH="main"

echo "=== Randebu Deployment Script ==="
echo "Deploy directory: $DEPLOY_DIR"
echo "Domain: $DOMAIN"
echo ""

cd "$DEPLOY_DIR"

echo "[1/6] Pulling latest code..."
git pull origin "$BRANCH"

echo "[2/6] Updating backend dependencies..."
cd "$DEPLOY_DIR/src/backend"
source venv/bin/activate
pip install -r requirements.txt

echo "[3/6] Rebuilding frontend..."
cd "$DEPLOY_DIR/src/frontend"
npm install
npm run build
mkdir -p "$DEPLOY_DIR/frontend"
cp -r build/* "$DEPLOY_DIR/frontend/"

echo "[4/6] Restarting backend service..."
sudo systemctl restart ave-backend
sleep 2
sudo systemctl status ave-backend --no-pager

echo "[5/6] Testing endpoints..."
curl -s "http://localhost:8000/health" && echo ""
curl -s -o /dev/null -w "Frontend: %{http_code}\n" "https://$DOMAIN/" || true

echo "[6/6] Verifying SSL..."
sudo certbot certificates 2>/dev/null | grep -A2 "$DOMAIN" || echo "No certificate found for $DOMAIN"

echo ""
echo "=== Deployment Complete ==="
echo "Backend: https://$DOMAIN/api/"
echo "Frontend: https://$DOMAIN/"
echo "Backend logs: sudo journalctl -u ave-backend -f"