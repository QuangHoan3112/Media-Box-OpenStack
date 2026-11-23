#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"
MODE="${1:---dry-run}"

source "$ROOT/scripts/deployment/safety.sh"
source "$DIR/network.env.example"

PRIVATE_GATEWAY="${PRIVATE_GATEWAY:-10.20.0.1}"
SSH_CIDR="${PRIVATE_GATEWAY}/32"

echo "===== MEDIABOX SECURITY GROUP DEPLOYMENT ====="

create_app_rules() {
  run openstack security group rule create \
    --ingress --ethertype IPv4 \
    --protocol tcp --dst-port 8000 \
    --remote-ip "$PRIVATE_CIDR" "$APP_SECURITY_GROUP"

  run openstack security group rule create \
    --ingress --ethertype IPv4 \
    --protocol tcp --dst-port 22 \
    --remote-ip "$SSH_CIDR" "$APP_SECURITY_GROUP"
}

create_db_rules() {
  run openstack security group rule create \
    --ingress --ethertype IPv4 \
    --protocol tcp --dst-port 5432 \
    --remote-group "$APP_SECURITY_GROUP" \
    "$DB_SECURITY_GROUP"

  run openstack security group rule create \
    --ingress --ethertype IPv4 \
    --protocol tcp --dst-port 22 \
    --remote-ip "$SSH_CIDR" "$DB_SECURITY_GROUP"
}

if [[ "$MODE" == "--dry-run" ]]; then
  run openstack security group create "$APP_SECURITY_GROUP"
  create_app_rules
  run openstack security group create "$DB_SECURITY_GROUP"
  create_db_rules
  exit 0
fi

if openstack security group show "$APP_SECURITY_GROUP" >/dev/null 2>&1; then
  echo "SKIP: application security group exists"
else
  run openstack security group create "$APP_SECURITY_GROUP"
  create_app_rules
fi

if openstack security group show "$DB_SECURITY_GROUP" >/dev/null 2>&1; then
  echo "SKIP: database security group exists"
else
  run openstack security group create "$DB_SECURITY_GROUP"
  create_db_rules
fi

echo "NOTE: verify existing rules and default egress rules."
echo "===== SECURITY GROUP DEPLOYMENT FINISHED ====="
