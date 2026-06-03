#!/bin/bash
# Shared settings for lab5 scripts (source from task scripts).

CORE_HOST="${CORE_HOST:-10.227.20.82}"
GNB_HOST="${GNB_HOST:-10.227.20.72}"
EXT_DN="${EXT_DN:-192.168.70.135}"
AMF_IP="${AMF_IP:-192.168.70.132}"
DOCKER_SUBNET="${DOCKER_SUBNET:-192.168.70.128/26}"
SSH_USER="${SSH_USER:-mobile}"
SUDO_PASS="${SUDO_PASS:-mobile}"

if [ -n "${SUDO_USER:-}" ]; then
    REAL_USER_HOME=$(getent passwd "${SUDO_USER}" | cut -d: -f6)
else
    REAL_USER_HOME="${HOME}"
fi

GNB_BUILD="${REAL_USER_HOME}/oai/cmake_targets/ran_build/build"
GNB_CONF="${REAL_USER_HOME}/oai/targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.fr1.106PRB.usrpb210.conf"
CORE_DIR="${REAL_USER_HOME}/oai-cn5g"
FLEXRIC_DIR="${REAL_USER_HOME}/flexric"
RIC_BIN="${FLEXRIC_DIR}/build/examples/ric/nearRT-RIC"
XAPP_KPM_RC="${FLEXRIC_DIR}/build/examples/xApp/c/kpm_rc/xapp_kpm_rc"

die() { echo "[FATAL] $*" >&2; exit 1; }

sudo_cmd() {
    echo "${SUDO_PASS}" | sudo -S "$@"
}

cleanup_task6_sessions() {
    for s in task6_ric task6_gnb task6_ue task6_xapp; do
        tmux kill-session -t "$s" 2>/dev/null || true
    done
}

wait_log() {
    local file="$1" pattern="$2" timeout="${3:-120}"
    local i=0
    while [ "$i" -lt "$timeout" ]; do
        if [ -f "$file" ] && grep -qE "$pattern" "$file"; then
            return 0
        fi
        sleep 1
        i=$((i + 1))
    done
    return 1
}

setup_gnb_network() {
  local uplink="${UPLINK_IFACE:-eno1}"
  echo "[config] gNB route to Core subnet via ${CORE_HOST}..."
  sudo_cmd ip route del "${DOCKER_SUBNET}" 2>/dev/null || true
  sudo_cmd ip route add "${DOCKER_SUBNET}" via "${CORE_HOST}" dev "${uplink}"
  sudo_cmd sysctl -w net.ipv4.conf.all.forwarding=1 >/dev/null
  sudo_cmd iptables -P FORWARD ACCEPT 2>/dev/null || true
}

wait_for_core() {
  local i=0
  while [ "$i" -lt 60 ]; do
    if ping -c 1 -W 1 "${AMF_IP}" >/dev/null 2>&1; then
      echo "[config] AMF ${AMF_IP} reachable."
      return 0
    fi
    sleep 2
    i=$((i + 2))
  done
  echo "[config] WARN: AMF not reachable yet."
  return 1
}
