#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"
MODE="${1:---dry-run}"

source "$ROOT/scripts/deployment/safety.sh"
source "$DIR/network.env.example"

PRIVATE_GATEWAY="${PRIVATE_GATEWAY:-10.20.0.1}"

echo "===== MEDIABOX NETWORK DEPLOYMENT ====="

if [[ "$MODE" == "--dry-run" ]]; then
  echo "PREREQUISITE: provider network $PUBLIC_NETWORK"
  run openstack network create --internal "$PRIVATE_NETWORK"
  run openstack subnet create \
    --network "$PRIVATE_NETWORK" \
    --subnet-range "$PRIVATE_CIDR" \
    --gateway "$PRIVATE_GATEWAY" \
    --dhcp "$PRIVATE_SUBNET"
  run openstack router create \
    --external-gateway "$PUBLIC_NETWORK" \
    --enable-snat "$ROUTER_NAME"
  run openstack router add subnet \
    "$ROUTER_NAME" "$PRIVATE_SUBNET"
  exit 0
fi

openstack network show "$PUBLIC_NETWORK" >/dev/null

if openstack network show "$PRIVATE_NETWORK" >/dev/null 2>&1; then
  echo "SKIP: private network already exists"
else
  run openstack network create --internal "$PRIVATE_NETWORK"
fi

if openstack subnet show "$PRIVATE_SUBNET" >/dev/null 2>&1; then
  ACTUAL=$(openstack subnet show "$PRIVATE_SUBNET" \
    -c cidr -f value)
  [[ "$ACTUAL" == "$PRIVATE_CIDR" ]] || {
    echo "STOP: existing subnet CIDR mismatch"
    exit 1
  }
  echo "SKIP: private subnet already exists"
else
  run openstack subnet create \
    --network "$PRIVATE_NETWORK" \
    --subnet-range "$PRIVATE_CIDR" \
    --gateway "$PRIVATE_GATEWAY" \
    --dhcp "$PRIVATE_SUBNET"
fi

if openstack router show "$ROUTER_NAME" >/dev/null 2>&1; then
  echo "SKIP: existing router; verify gateway and interface manually"
else
  run openstack router create \
    --external-gateway "$PUBLIC_NETWORK" \
    --enable-snat "$ROUTER_NAME"

  run openstack router add subnet \
    "$ROUTER_NAME" "$PRIVATE_SUBNET"
fi

echo "===== NETWORK DEPLOYMENT FINISHED ====="
