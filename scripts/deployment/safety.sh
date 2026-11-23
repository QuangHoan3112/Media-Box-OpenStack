#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:---dry-run}"

case "$MODE" in
  --dry-run|--apply) ;;
  *) echo "Usage: --dry-run | --apply"; exit 2 ;;
esac

if [[ "$MODE" == "--apply" ]]; then
  if [[ "${MEDIABOX_NEW_CLOUD_CONFIRM:-}" != YES ||
        -z "${OS_CLOUD:-}" ||
        "${OS_CLOUD}" == "kolla-admin" ]]; then
    echo "REFUSED: deployment requires a separate new cloud."
    exit 2
  fi
fi

run() {
  printf '+'
  printf ' %q' "$@"
  printf '\n'

  if [[ "$MODE" == "--apply" ]]; then
    "$@"
  fi
}
