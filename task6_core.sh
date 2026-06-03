#!/bin/bash
# Run on Core (tux82): start OAI 5GC Docker stack.
set -eu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

cd "${CORE_DIR}" || die "Missing ${CORE_DIR}"
echo "[task6_core] Starting 5G Core..."
sudo_cmd docker compose up -d
sleep 5
sudo_cmd docker compose ps
echo "[task6_core] Core is up."
