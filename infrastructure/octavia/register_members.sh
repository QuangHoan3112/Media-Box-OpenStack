#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"
MODE="${1:---dry-run}"

source "$ROOT/scripts/deployment/safety.sh"
source "$DIR/loadbalancer.env.example"

APP01_IP="${APP01_IP:-}"
APP02_IP="${APP02_IP:-}"

echo "===== REGISTER FIXED APP SERVERS ====="

if [[ -z "$APP01_IP" || -z "$APP02_IP" ]]; then
  echo "Set APP01_IP and APP02_IP from the new deployment."
  echo "Example:"
  echo "APP01_IP=10.20.0.89 APP02_IP=10.20.0.212 bash $0 --dry-run"
  exit 0
fi

for IP in "$APP01_IP" "$APP02_IP"; do
  if [[ "$MODE" == "--apply" ]]; then
    if openstack loadbalancer member list "$LB_POOL_NAME" \
      -c address -f value | grep -Fxq "$IP"; then
      echo "SKIP: existing backend $IP"
      continue
    fi
  fi

  run openstack loadbalancer member create \
    --address "$IP" \
    --protocol-port 8000 \
    --subnet-id "$PRIVATE_SUBNET" \
    --wait "$LB_POOL_NAME"
done

echo "NOTE: Heat-managed backends are registered by their deployment workflow."
echo "===== MEMBER REGISTRATION FINISHED ====="
