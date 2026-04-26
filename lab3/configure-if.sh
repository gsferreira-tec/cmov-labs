#!/usr/bin/bash 

#set -x
set -euo pipefail

if [ $# -ne 1 ]; then
	echo "Usage: $0 <host_number>"
	exit 1
fi

HOSTNO=$1

echo "Configuring interface(s)..."
sleep 1
echo

case "$HOSTNO"
in
	1)
	echo "Configuring interfaces h1-eth0 and h1-eth1 for Host ${HOSTNO}..."
	ifconfig h${HOSTNO}-eth0 inet6 add 2029::$HOSTNO/128
	ifconfig h${HOSTNO}-eth1 up
	ifconfig h${HOSTNO}-eth1 inet6 add 3000::9/64
	;;
	2|3|4)	
	echo "Configuring interface h${HOSTNO}-eth0 for Host ${HOSTNO}..."
	ifconfig h${HOSTNO}-eth0 inet6 add 2029::$HOSTNO/128
	;;
	5) 
	echo "Configuring interface h${HOSTNO}-eth0 for Host ${HOSTNO}..."
	ifconfig h${HOSTNO}-eth0 inet6 add 3000::254/64
	route -A inet6 add 2029:0:0::/64 gw 3000::
	;;
	*)
	echo "Host number unknown."
	exit 1
	;; 
esac
sleep 1
echo
echo "Interface(s) configured for host ${HOSTNO}."
sleep 1
