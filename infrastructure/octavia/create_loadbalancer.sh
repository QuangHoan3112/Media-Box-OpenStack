#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"
MODE="${1:---dry-run}"

source "$ROOT/scripts/deployment/safety.sh"
source "$DIR/loadbalancer.env.example"

echo "===== MEDIABOX OCTAVIA DEPLOYMENT ====="

create_resources() {
  run openstack loadbalancer create \
    --name "$LB_NAME" \
    --vip-subnet-id "$PRIVATE_SUBNET" \
    --wait

  run openstack loadbalancer listener create \
    --name "$LB_LISTENER_NAME" \
    --protocol HTTP \
    --protocol-port 8000 \
    --wait "$LB_NAME"

  run openstack loadbalancer pool create \
    --name "$LB_POOL_NAME" \
    --protocol HTTP \
    --lb-algorithm ROUND_ROBIN \
    --listener "$LB_LISTENER_NAME" \
    --wait

  run openstack loadbalancer healthmonitor create \
    --name "$LB_HEALTH_MONITOR_NAME" \
    --type HTTP \
    --http-method GET \
    --url-path /health \
    --expected-codes 200 \
    --delay 5 \
    --timeout 3 \
    --max-retries 3 \
    --max-retries-down 3 \
    --wait "$LB_POOL_NAME"
}

if [[ "$MODE" == "--dry-run" ]]; then
  create_resources
  exit 0
fi

openstack subnet show "$PRIVATE_SUBNET" >/dev/null

if openstack loadbalancer show "$LB_NAME" >/dev/null 2>&1; then
  echo "SKIP: load balancer exists."
  echo "Inspect listener, pool and monitor before making changes."
  exit 0
fi

create_resources

echo "===== OCTAVIA DEPLOYMENT FINISHED ====="
