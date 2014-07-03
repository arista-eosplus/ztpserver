#!/bin/bash

#Assume that we are using Fusion
cd /Applications/VMware\ Fusion.app/Contents/Library/

#Check the current status
printf "Starting the VMware network setup....\n\nCurrent VMware Fusion current network setup\n-------------------------------------\n"
./vmnet-cli --status

#Create an array with the vmnets we want to create/modify
declare -a VMNETS
VMNETS=(2 3 4 5 6 7 9 10 11)

for i in "${VMNETS[@]}"; do
  printf "Creating/Modifying vmnet$i\n"
  NET=$(($i+128))
  ./vmnet-cfgcli vnetcfgadd VNET_${i}_DHCP no
  ./vmnet-cfgcli vnetcfgadd VNET_${i}_HOSTONLY_SUBNET 172.16.${NET}.0
  ./vmnet-cfgcli vnetcfgadd VNET_${i}_HOSTONLY_NETMASK 255.255.255.0
  ./vmnet-cfgcli vnetcfgadd VNET_${i}_VIRTUAL_ADAPTER yes
done

./vmnet-cli --configure
./vmnet-cli --stop
./vmnet-cli --start
sleep 2
./vmnet-cli --status
