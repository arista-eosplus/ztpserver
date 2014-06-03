#!/bin/sh -x

#Install ztps-related related packages
yum -y install gcc make gcc-c++
yum -y install pip
yum -y install git
yum -y install net-tools
yum -y install dhcp
yum -y install bind
yum -y install ejabberd