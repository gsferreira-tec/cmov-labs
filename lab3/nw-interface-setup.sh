#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo "No host number provided."
	echo "##############################"
	echo "Usage: sudo $0 <host_number>"
	exit 1
fi

HOST_NO=$1

# if the necessary arguments were provided then run the commands
PATH="/proc/sys/net/ipv6/conf/h${HOST_NO}-eth0"

# and if the target files exist
if [ ! -d "$PATH" ]; then
	echo "[ERROR] $PATH does not exist - check that the host number is correct."
	exit 1
fi

echo 0 >  "$PATH/accept_ra"  # disables RA messages
echo 1 >  "$PATH/forwarding" # enable IPv6 forwarding

echo
echo "IPv6 interface on h${HOST_NO}-eth0 configured successfully."


