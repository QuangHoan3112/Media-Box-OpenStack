#!/bin/bash
set -euo pipefail

exec > >(tee -a /var/log/mediabox-bootstrap.log) 2>&1

echo "MEDIABOX_BOOTSTRAP_STARTED"

export DEBIAN_FRONTEND=noninteractive

# MediaBox dependency download proxy
export http_proxy="http://192.168.57.254:8888"
export https_proxy="$http_proxy"
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$https_proxy"
export no_proxy="localhost,127.0.0.1,10.20.0.0/24"
export NO_PROXY="$no_proxy"

apt-get update
apt-get install -y python3-venv python3-pip curl

install -d -o ubuntu -g ubuntu \
  /home/ubuntu/mediabox-app

install -d -m 700 -o ubuntu -g ubuntu \
  /home/ubuntu/.config/mediabox

printf '%s' '__APP_TAR_B64__' | base64 -d | tar -xz -C /home/ubuntu/mediabox-app

printf '%s' '__APP_ENV_B64__' | base64 -d > /home/ubuntu/.config/mediabox/app.env

chmod 600 /home/ubuntu/.config/mediabox/app.env
chown -R ubuntu:ubuntu /home/ubuntu/mediabox-app
chown -R ubuntu:ubuntu /home/ubuntu/.config/mediabox

python3 -m venv /home/ubuntu/mediabox-app/.venv

/home/ubuntu/mediabox-app/.venv/bin/pip \
  install --no-cache-dir \
  -r /home/ubuntu/mediabox-app/requirements.txt

cat > /etc/systemd/system/mediabox-app.service <<'SERVICE'
[Unit]
Description=MediaBox FastAPI Application
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/mediabox-app
EnvironmentFile=/home/ubuntu/.config/mediabox/app.env
ExecStart=/home/ubuntu/mediabox-app/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now mediabox-app.service

for i in $(seq 1 30); do
  if curl -fsS --max-time 5 http://127.0.0.1:8000/health; then
    echo "MEDIABOX_BOOTSTRAP_SUCCESS"
    exit 0
  fi
  sleep 2
done

echo "MEDIABOX_HEALTH_CHECK_FAILED"
exit 1
