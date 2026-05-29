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

# Killing previous Task 1 occurences
tmux kill-session -t gnb 2>/dev/null
tmux kill-session -t ue 2>/dev/null

# Killing previous Task 2 occurences
tmux kill-session -t ue1 2>/dev/null
tmux kill-session -t ue2 2>/dev/null

if [ "$1" == "gnb" ]; then 

	cd ~/oai/cmake_targets/ran_build/build

	echo "[*] Starting gNB"
	tmux new-session -d -s gnb \
	"sudo ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.fr1.106PRB.usrpb210.conf --gNBs.[0].min_rxtxtime 6 --rfsim --sa"

	sleep 10

	########################
	#        TASK 1        #
	########################
	
	if [ "$2" == "1" ] || [ "$2" == "one" ]; then
		echo "[*] Starting UE"

		tmux new-session -d -s ue \
	        "sudo ./nr-uesoftmodem -r 106 --numerology 1 --band 78 -C 3619200000 --rfsim --sa --uicc0.imsi 001010000000001 --rfsimulator.serveraddr 127.0.0.1"


                #cd ~/oai/ci-scripts/yaml_files/5g_rfsimulator/docker-compose.yaml
		#echo "[*] Bringing up oai-nr-ue1"
		#docker compose -f docker-compose.yaml up -d oai-nr-ue1

		sleep 10

		echo "[*] Pinging Uplink 10 times"
		ping -c 10 $IP_EXT_DN -I oaitun_ue1 

		IP_UE=$(ip addr show oaitun_ue1 | grep "inet " | awk '{print $2}' | cut -d/ -f1)

		echo "IP of UE1: $IP_UE"

		sleep 5

		echo "[*] Pinging Downlink 10 times"
		ssh -t mobile@${IP_HOST_CORE} "sudo docker exec oai-ext-dn ping -c 10 $IP_UE"
		#sshpass -p 'mobile' ssh -o StrictHostKeyChecking=no mobile@${IP_HOST_CORE} "sudo docker exec oai-ext-dn ping -c 10 $IP_UE" # To instantly pass the password login

		

	########################
	#        TASK 2        #
	########################
	elif [ "$2" == "2" ] || [ "$2" == "two" ]; then

		chmod +x ~/multi-ue.sh  

		echo "[*] Creating Namespaces for UE1 and UE2"
		sudo ~/multi-ue.sh -c1
		sudo ~/multi-ue.sh -c2

		echo "[*] Starting UE1 in namespace ue1"
		tmux new-session -d -s ue1 \
		    "sudo ip netns exec ue1 ./nr-uesoftmodem -r 106 --numerology 1 --band 78 -C 3619200000 --rfsim --sa --uicc0.imsi 001010000000001 --rfsimulator.serveraddr 10.201.1.100 --telnetsrv --telnetsrv.listenport 9095"

		echo "[*] Starting UE2 in namespace ue2"
		tmux new-session -d -s ue2 \
		    "sudo ip netns exec ue2 ./nr-uesoftmodem -r 106 --numerology 1 --band 78 -C 3619200000 --rfsim --sa --uicc0.imsi 001010000000002 --rfsimulator.serveraddr 10.202.1.100 --telnetsrv --telnetsrv.listenport 9096"

		sleep 10 # Giving time for UEs to start		

		echo "[*] Pinging Uplink 10 times from UE1"
		sudo ip netns exec ue1 ping -c 10 $IP_EXT_DN -I oaitun_ue1 

		echo "[*] Pinging Uplink 10 times from UE2"
		sudo ip netns exec ue2 ping -c 10 $IP_EXT_DN -I oaitun_ue1 # UE2 gets associated still to "oaitun_ue1"

		IP_UE1=$(sudo ip netns exec ue1 ip addr show oaitun_ue1 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
		IP_UE2=$(sudo ip netns exec ue2 ip addr show oaitun_ue1 | grep "inet " | awk '{print $2}' | cut -d/ -f1) # UE2 gets associated still to "oaitun_ue1"

		echo "IP of UE1: $IP_UE1"
		echo "IP of UE2: $IP_UE2"

		sleep 5

		echo "[*] Pinging Downlink 10 times to UE1"
		ssh -t mobile@${IP_HOST_CORE} "sudo docker exec oai-ext-dn ping -c 10 $IP_UE1"
		#sshpass -p 'mobile' ssh -o StrictHostKeyChecking=no mobile@${IP_HOST_CORE} "sudo docker exec oai-ext-dn ping -c 10 $IP_UE1" 


		echo "[*] Pinging Downlink 10 times to UE2"
		ssh -t mobile@${IP_HOST_CORE} "sudo docker exec oai-ext-dn ping -c 10 $IP_UE2"
		#sshpass -p 'mobile' ssh -o StrictHostKeyChecking=no mobile@${IP_HOST_CORE} "sudo docker exec oai-ext-dn ping -c 10 $IP_UE2"

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
		sudo timeout 120 tcpdump -i any "udp port 2152 or host ${IP_EXT_DN}" -U -w ${FILE_PATH}dl-ul-pings-task1.pcap


	########################
	#        TASK 2        #
	########################
	elif [ "$2" == "2" ] || [ "$2" == "two" ]; then
		sudo rm ${FILE_PATH}dl-ul-pings-task2.pcap

		echo "[*] Listening for ${IP_EXT_DN} IP for Task 2 communicatin with UE1 and then UE2"
		sudo timeout 180 tcpdump -i any "udp port 2152 or host ${IP_EXT_DN}" -U -w ${FILE_PATH}dl-ul-pings-task2.pcap
	
	

	########################
	#        TASK 3        #
	########################
	
	elif [ "$3" == "3" ] || [ "$3" == "three" ]; then
		echo "Empty"

	fi

else
	echo "Usage: ./$0 <gnb/core> <(1|one)/(2|two)>"
	exit 1
fi
