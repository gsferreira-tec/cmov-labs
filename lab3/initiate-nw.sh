#!/usr/bin/bash
# This scrip can be used to initiate the netowrk without having to write this huge command
echo "Initializing the network..."
echo
sleep 1
sudo mn -x --switch=ovsbr --controller=none --custom=/home/guilherme/Desktop/MEEC/2Sem/CMOV/Lab3-Submission/mininet_olsr_topology.py --topo=olsr_topo
sleep 1
echo 
echo "Network connection broken! Bye! \O/"
