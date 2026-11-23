#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"
MODE="${1:---dry-run}"

source "$ROOT/scripts/deployment/safety.sh"
source "$DIR/storage.env.example"

echo "===== MEDIABOX STORAGE DEPLOYMENT ====="

if [[ "$MODE" == "--dry-run" ]]; then
  run openstack container create "$SWIFT_CONTAINER"

  run openstack volume create \
    --size "$DB_VOLUME_SIZE_GB" \
    "$DB_VOLUME_NAME"

  echo "No resources created."
  exit 0
fi

echo "===== SWIFT ====="

if openstack container show "$SWIFT_CONTAINER" \
  >/dev/null 2>&1; then
  echo "SKIP: Swift container exists"
else
  run openstack container create "$SWIFT_CONTAINER"
fi

echo "===== CINDER ====="

MATCHES=$(
  openstack volume list -c Name -f value |
    grep -Fxc "$DB_VOLUME_NAME" || true
)

if [[ "$MATCHES" -gt 1 ]]; then
  echo "STOP: duplicate volume names"
  exit 1
elif [[ "$MATCHES" -eq 1 ]]; then
  ACTUAL_SIZE=$(
    openstack volume show "$DB_VOLUME_NAME" \
      -c size -f value
  )

  if [[ "$ACTUAL_SIZE" != "$DB_VOLUME_SIZE_GB" ]]; then
    echo "STOP: existing volume size differs"
    exit 1
  fi

  echo "SKIP: Cinder volume exists"
else
  run openstack volume create \
    --size "$DB_VOLUME_SIZE_GB" \
    "$DB_VOLUME_NAME"
fi

echo "NOTE: volume attachment is not automated."
echo "NOTE: no filesystem or database was modified."
echo "===== STORAGE DEPLOYMENT FINISHED ====="
