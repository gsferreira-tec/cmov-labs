#!/usr/bin/bash

if [ $# -ne 1 ]; then
	echo "Usage: $0 <host_number>"
	exit 1
fi

HOSTNO=$1
OLSRD_FILE="/etc/olsrd/olsrd${HOSTNO}.conf"

echo "Initiating the OLSR network..."
sleep 1
olsrd -f $OLSRD_FILE -d 0
sleep 1 
echo
echo "Done. Host ${HOSTNO} running OLSR."
