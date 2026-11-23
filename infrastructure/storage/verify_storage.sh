#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/storage.env.example"

echo "===== SWIFT CONTAINER ====="

openstack container show "$SWIFT_CONTAINER" \
  -c name -f yaml

echo "===== SWIFT OBJECT COUNT ====="

COUNT=$(
  openstack object list "$SWIFT_CONTAINER" \
    -c Name -f value | awk 'END {print NR}'
)

echo "OBJECT_COUNT=$COUNT"
echo "Object names and contents are not printed."

echo "===== CINDER DB VOLUME ====="

openstack volume show "$DB_VOLUME_NAME" \
  -c name \
  -c size \
  -c status \
  -c attachments \
  -f yaml

echo "===== DATABASE VM ====="

openstack server show "$DB_INSTANCE_NAME" \
  -c name \
  -c status \
  -c addresses \
  -f yaml

echo "===== STORAGE VERIFICATION COMPLETE ====="
