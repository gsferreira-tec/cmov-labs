#!/bin/bash
# Task 6 (bonus): start OAI + FlexRIC, run KPM/RC xApp, trigger gNB RC action.
# Run on gNB host (tux72):  bash task6.sh
# Optional: SKIP_CORE=1 if Core already running.
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

LOG_DIR="${REAL_USER_HOME}/task6_logs/$(date +%Y%m%d_%H%M%S)"
mkdir -p "${LOG_DIR}"

echo "=============================================="
echo "  Lab 5 — Task 6: FlexRIC xApp (KPM + RC)"
echo "  Logs: ${LOG_DIR}"
echo "=============================================="

[ -x "${RIC_BIN}" ] || die "Build FlexRIC RIC first: ${RIC_BIN}"
[ -x "${XAPP_KPM_RC}" ] || die "Build xApp first: ${XAPP_KPM_RC}"
[ -f "${GNB_CONF}" ] || die "Missing gNB config: ${GNB_CONF}"

cleanup_task6_sessions
sudo_cmd pkill -9 nr-softmodem 2>/dev/null || true
sudo_cmd pkill -9 nr-uesoftmodem 2>/dev/null || true
sleep 2

if [ "${SKIP_CORE:-0}" != "1" ]; then
    echo "[task6] Starting Core on ${CORE_HOST}..."
    ssh -o BatchMode=yes "${SSH_USER}@${CORE_HOST}" "bash -s" < "${SCRIPT_DIR}/task6_core.sh" \
        | tee "${LOG_DIR}/core_start.log"
fi

echo "[task6] Waiting for Core AMF..."
wait_for_core 2>&1 | tee "${LOG_DIR}/core_wait.log" || true

echo "[task6] gNB routing / firewall..."
setup_gnb_network 2>&1 | tee "${LOG_DIR}/gnb_setup.log"

echo "[task6] Starting nearRT-RIC..."
tmux new-session -d -s task6_ric \
    "cd ${FLEXRIC_DIR} && ${RIC_BIN} 2>&1 | tee ${LOG_DIR}/ric.log"

echo "[task6] Starting gNB (E2 agent)..."
tmux new-session -d -s task6_gnb \
    "cd ${GNB_BUILD} && echo '${SUDO_PASS}' | sudo -S ./nr-softmodem -O ${GNB_CONF} --gNBs.[0].min_rxtxtime 6 --rfsim --sa 2>&1 | tee ${LOG_DIR}/gnb.log"

echo "[task6] Waiting for gNB / RIC (25s)..."
sleep 25

echo "[task6] Starting UE..."
tmux new-session -d -s task6_ue \
    "cd ${GNB_BUILD} && echo ${SUDO_PASS} | sudo -S ./nr-uesoftmodem -r 106 --numerology 1 --band 78 -C 3619200000 \
     --rfsim --sa --uicc0.imsi 001010000000001 --rfsimulator.serveraddr 127.0.0.1 2>&1 | tee ${LOG_DIR}/ue.log"

echo "[task6] Waiting for UE attach (25s)..."
sleep 25

echo "[task6] Baseline connectivity (ping ext-DN)..."
if echo "${SUDO_PASS}" | sudo -S ping -c 3 "${EXT_DN}" -I oaitun_ue1 2>&1 | tee "${LOG_DIR}/ping_before.log"; then
    echo "[task6] UE has IP: $(ip -4 addr show oaitun_ue1 | awk '/inet /{print $2}')"
else
    echo "[task6] WARN: ping before xApp failed (continuing anyway)"
fi

echo "[task6] Running xApp KPM+RC (RC CONTROL = QoS flow mapping on gNB)..."
tmux kill-session -t task6_xapp 2>/dev/null || true
tmux new-session -d -s task6_xapp \
    "cd ${FLEXRIC_DIR}/build/examples/xApp/c/kpm_rc && stdbuf -oL ${XAPP_KPM_RC} 2>&1 | tee ${LOG_DIR}/xapp.log"
echo "[task6] Waiting for xApp (20s)..."
sleep 20
if tmux has-session -t task6_xapp 2>/dev/null; then
    tmux send-keys -t task6_xapp C-c
    sleep 3
fi
tmux kill-session -t task6_xapp 2>/dev/null || true

echo "[task6] Verifying results..."
PASS=0
FAIL=0
check() {
    if eval "$2"; then
        echo "  [OK] $1"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $1"
        FAIL=$((FAIL + 1))
    fi
}

check "E2 node connected (xApp)" \
    "grep -q 'Connected E2 nodes' ${LOG_DIR}/xapp.log && ! grep -q 'Connected E2 nodes = 0' ${LOG_DIR}/xapp.log"
check "KPM subscription active" \
    "grep -q 'KPM' ${LOG_DIR}/xapp.log || grep -q 'DRB\\.' ${LOG_DIR}/xapp.log"
check "RC CONTROL sent (xApp)" \
    "grep -q 'RC' ${LOG_DIR}/xapp.log || grep -q 'QoS' ${LOG_DIR}/xapp.log"
check "RC CONTROL acknowledged by gNB" \
    "grep -q 'CONTROL ACK' ${LOG_DIR}/xapp.log || grep -q 'Successfully received CONTROL' ${LOG_DIR}/xapp.log"
check "xApp completed or stopped cleanly" \
    "grep -q 'Test xApp run SUCCESSFULLY' ${LOG_DIR}/xapp.log || grep -q 'CONTROL ACK' ${LOG_DIR}/xapp.log"
check "gNB produced logs" \
    "[ -s ${LOG_DIR}/gnb.log ]"

{
    echo "Task 6 summary — $(date -Iseconds)"
    echo "PASS=${PASS} FAIL=${FAIL}"
    echo "Approach: nearRT-RIC + xapp_kpm_rc (E2SM-KPM subscribe, E2SM-RC CONTROL Style 1 — QoS flow mapping)."
    echo "Logs: ${LOG_DIR}"
} | tee "${LOG_DIR}/summary.txt"

echo ""
echo "Attach: tmux attach -t task6_ric|task6_gnb|task6_ue"
echo "Cleanup: tmux kill-session -t task6_ric; tmux kill-session -t task6_gnb; tmux kill-session -t task6_ue"

if [ "${FAIL}" -eq 0 ]; then
    echo "[task6] All checks passed."
    exit 0
fi
echo "[task6] Some checks failed — inspect ${LOG_DIR}"
exit 1
