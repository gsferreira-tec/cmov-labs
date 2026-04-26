#!/usr/bin/env bash

#set -x
set -euo pipefail

if [ $# -ne 1 ]; then
	echo "Usage: $0 <exercise_number>"
	help
	exit 1
fi	

help() {
	echo "Available Exercise Modes:"
	echo 
	echo "	- 2.5 - for the topology change"
	echo "	- 2.6 - for the HNA configuration"
	echo
}

echo "Creating olsrd.conf copies for all hosts..."

OLSRD_PATH="/etc/olsrd"

# this loop essentially just comments everything out from the copy
for i in {1..5}; do
	cp $OLSRD_PATH/olsrd.conf $OLSRD_PATH/olsrd${i}.conf
	sed -i "s/LinkQualityFishEye/#LinkQualityFishEye/g" $OLSRD_PATH/olsrd${i}.conf
	sed -i "s/Interface/#Interface/g" $OLSRD_PATH/olsrd${i}.conf
	sed -i "s/{/#/g" $OLSRD_PATH/olsrd${i}.conf
	sed -i "s/}/#/g" $OLSRD_PATH/olsrd${i}.conf
	sed -i "s/LoadPlugin/#LoadPlugin/g" $OLSRD_PATH/olsrd${i}.conf
	sed -i "s/PlParam/#PlParam/g" $OLSRD_PATH/olsrd${i}.conf
	cat -n $OLSRD_PATH/olsrd${i}.conf | grep -i '#'
	sleep 1
done

echo "[*] Copies created."

sleep 1 

echo
echo "Appending the interface block..."

for i in {1..5}; do 
cat << EOF >> $OLSRD_PATH/olsrd${i}.conf


#-----------------------------------------
#   Added Configuration/Interface Block
#-----------------------------------------

DebugLevel	1
IpVersion	6
LinkQualityLevel	0
MprCoverage	1

Interface = "h${i}-eth0" {
        HelloInterval   6.0
        HelloValidityTime       60.0 
        TcInterval      10.0
        TcValidityTime  60.0
        HnaInterval     10.0
        HnaValidityTime 60.0
}
# ----------------------------------------
EOF

done

mode=$1

for i in {1..5}; do
if [ $mode = "2.6" ]; then
	break
elif [ $mode = "2.5" ]; then
	sed -i "s/Hna/#Hna/g" $OLSRD_PATH/olsrd${i}.conf
	cat -n $OLSRD_PATH/olsrd${i}.conf | grep -i "#"
else
	echo
	echo "Default selection - setup for exercise 2.6."
	echo
fi
echo "- olsrd${i}.conf prepared"
sleep 1
done

echo "[*] Configuration files ready."

