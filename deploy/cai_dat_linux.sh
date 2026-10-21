#!/usr/bin/env bash
# Cài đặt tự động trên Ubuntu/Debian. Chạy:  sudo bash deploy/cai_dat_linux.sh [tên-miền]
set -euo pipefail
DOMAIN="${1:-dutoan.example.vn}"
APP_DIR=/opt/dutoan
REPO=https://github.com/hs5011/UngDungXuatDuToan.git

apt update
apt install -y python3 python3-venv python3-pip git nginx

if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull
else
  git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p workspace
chown -R www-data "$APP_DIR/workspace"

cp deploy/dutoan.service /etc/systemd/system/dutoan.service
systemctl daemon-reload
systemctl enable --now dutoan

sed "s/dutoan.example.vn/$DOMAIN/" deploy/nginx-dutoan.conf > /etc/nginx/sites-available/dutoan
ln -sf /etc/nginx/sites-available/dutoan /etc/nginx/sites-enabled/dutoan
nginx -t && systemctl reload nginx

echo "Xong. Mở http://$DOMAIN . HTTPS: sudo certbot --nginx -d $DOMAIN"
echo "Đặt mật khẩu: sudo apt install apache2-utils && sudo htpasswd -c /etc/nginx/.htpasswd <user>, rồi bỏ comment auth_basic trong /etc/nginx/sites-available/dutoan"
