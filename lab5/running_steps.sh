#!/bin/bash 

IP_HOST_CORE="10.227.20.82"

IP_HOST_GNB="10.227.20.72"

IP_DOCKER_CORE_SUBNET="192.168.70.128/26"
IP_AMF="192.168.70.132"
IP_EXT_DN="192.168.70.135"
IP_UE="10.0.0.3"

FILE_PATH="/tmp/"

CONF_PATH=~/oai/targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.fr1.106PRB.usrpb210.conf
CONF_PATH_TMP=/tmp/gnb_task3.conf

if [ "$1" == "gnb" ]; then
	cd ~/oai/cmake_targets/ran_build/build

	echo "[*] Starting gNB"
	tmux new-session -d -s gnb \
	"sudo ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.fr1.106PRB.usrpb210.conf --gNBs.[0].min_rxtxtime 6 --rfsim --sa"

	########################
	#        TASK 1        #
	########################
	
	if [ "$2" == "1" ] || [ "$2" == "one" ]; then
		echo "[*] Starting UE"
		tmux new-session -d -s ue \
	        "sudo ./nr-uesoftmodem -r 106 --numerology 1 --band 78 -C 3619200000 --rfsim --sa --uicc0.imsi 001010000000001 --rfsimulator.serveraddr 127.0.0.1"

		sleep 10 # Giving time for UE to start

		echo "[*] Pinging Uplink 10 times"
		ping -c 10 $IP_EXT_DN -I oaitun_ue1 

		sleep 5

		echo "[*] Pinging Downlink 10 times"
		sudo docker exec -it oai-ext-dn ping -c 10 $IP_UE 
		

	########################
	#        TASK 2        #
	########################
	elif [ "$2" == "2" ] || [ "$2" == "two" ]; then

		echo "[*] Making sure we have the latest release for nrUE"
		sudo docker pull oaisoftwarealliance/oai-nr-ue:latest

		echo "[*] Deploying UE1 and UE2"
		docker compose up -d oai-nr-ue{1,2}

		echo "IP of UE1:"
		docker logs oai-nr-ue1

		echo "IP of UE2:"
		docker logs oai-nr-ue2

                echo "[*] Pinging Uplink 10 times from UE1"
		docker exec -it oai-nr-ue1 ping -c 10 $IP_EXT_DN

                echo "[*] Pinging Uplink 10 times from UE2"
		docker exec -it oai-nr-ue2 ping -c 10 $IP_EXT_DN

		echo "[*] Stopping the UEs"
		docker compose stop oai-nr-ue{1,2}
	#	docker compose down -v

	########################
	#        TASK 3        #
	########################
	
	elif [ "$3" == "3" ] || [ "$3" == "three" ]; then

		cp "$CONF_PATH" "$CONF_TMP"

		echo "[*] Changing gNB settings to 3500MHz center frequency and 100MHz bandwidth"
		
		sed -i '/#/!s/^\([[:space:]]*absoluteFrequencySSB[[:space:]]*=[[:space:]]*\).*$/\1 6300000;/' "$CONF_PATH_TMP"  # absoluteFrequencySSB = 630000

		sed -i '/#/!s/^\([[:space:]]*dl_absoluteFrequencyPointA[[:space:]]*=[[:space:]]*\).*$/\1 626724;/' "$CONF_PATH_TMP"  # dl_absoluteFrequencyPointA = 626724

		sed -i '/#/!s/^\([[:space:]]*dl_frequencyBand[[:space:]]*=[[:space:]]*\).*$/\1 78;/' "$CONF_PATH_TMP"  # dl_frequencyBand = 78

		sed -i '/#/!s/^\([[:space:]]*dl_subcarrierSpacing[[:space:]]*=[[:space:]]*\).*$/\1 1;/' "$CONF_PATH_TMP"  # dl_subcarrierSpacing = 1 (30 kHz)

		sed -i '/#/!s/^\([[:space:]]*dl_carrierBandwidth[[:space:]]*=[[:space:]]*\).*$/\1 106;/' "$CONF_PATH_TMP"  # dl_carrierBandwidth = 106 (100 MHz n78)

		sed -i '/#/!s/^\([[:space:]]*initialDLBWPlocationAndBandwidth[[:space:]]*=[[:space:]]*\).*$/\1 28875;/' "$CONF_PATH_TMP"  # initialDLBWPlocationAndBandwidth = 28875

		sed -i '/#/!s/^\([[:space:]]*initialDLBWPsubcarrierSpacing[[:space:]]*=[[:space:]]*\).*$/\1 1;/' "$CONF_PATH_TMP"  # initialDLBWPsubcarrierSpacing = 1

		sed -i '/#/!s/^\([[:space:]]*initialDLBWPcontrolResourceSetZero[[:space:]]*=[[:space:]]*\).*$/\1 12;/' "$CONF_PATH_TMP"  # CORESET0

		sed -i '/#/!s/^\([[:space:]]*ul_frequencyBand[[:space:]]*=[[:space:]]*\).*$/\1 78;/' "$CONF_PATH_TMP"  # ul_frequencyBand = 78

		sed -i '/#/!s/^\([[:space:]]*ul_carrierBandwidth[[:space:]]*=[[:space:]]*\).*$/\1 106;/' "$CONF_PATH_TMP"  # ul_carrierBandwidth = 106

		sed -i '/#/!s/^\([[:space:]]*initialULBWPlocationAndBandwidth[[:space:]]*=[[:space:]]*\).*$/\1 28875;/' "$CONF_PATH_TMP"  # initialULBWPlocationAndBandwidth = 28875

		sed -i '/#/!s/^\([[:space:]]*initialULBWPsubcarrierSpacing[[:space:]]*=[[:space:]]*\).*$/\1 1;/' "$CONF_PATH_TMP"  # initialULBWPsubcarrierSpacing = 1


	else 
		echo "Both gNB and UE were started"
	fi


elif [ "$1" == "core" ]; then
	cd ~/oai-cn5g

	echo "[*] Initiating Core"
	sudo docker compose up -d
	sudo docker ps

	########################
	#        TASK 1        #
	########################

	if [ "$2" == "1" ] || [ "$2" == "one" ]; then
		sudo rm ${FILE_PATH}dl-ul-pings-task1.pcap

		echo "[*] Listening for ${IP_EXT_DN} IP for Task 1 communicatin with one UE"
		sudo timeout 60 tcpdump host ${IP_EXT_DN} -w ${FILE_PATH}dl-ul-pings-task1.pcap



	########################
	#        TASK 2        #
	########################
	elif [ "$2" == "2" ] || [ "$2" == "two" ]; then
		sudo rm ${FILE_PATH}dl-ul-pings-task2.pcap

		echo "[*] Listening for ${IP_EXT_DN} IP for Task 2 communicatin with UE1 and then UE2"
		sudo timeout 60 tcpdump host ${IP_EXT_DN} -w ${FILE_PATH}dl-ul-pings-task2.pcap
	
	

	########################
	#        TASK 3        #
	########################
	
	elif [ "$3" == "3" ] || [ "$3" == "three" ]; then

	fi

else
	echo "Usage: ./$0 <gnb/core> <(1|one)/(2|two)>"
	exit 1
fi
