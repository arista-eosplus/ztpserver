#!/bin/sh -x

# Remove unnecessary packages
yum -y remove kbd

#Since we removed NetworkManager, let's setup the network service
systemctl stop NetworkManager.service
systemctl disable NetworkManager.service
systemctl restart network.service
systemctl enable network.service
yum -y remove NetworkManager

yum -y remove plymouth
yum -y remove uboot-tools

#Grab any updates and cleanup
yum --assumeyes update yum
yum --assumeyes update
yum --assumeyes clean all

#Install ztps-related related packages
yum -y install gcc make gcc-c++
yum -y install pip
yum -y install git
yum -y install net-tools
yum -y install dhcp
yum -y install bind
yum -y install ejabberd