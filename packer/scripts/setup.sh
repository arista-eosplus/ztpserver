#!/bin/sh -x

# Remove unnecessary packages
yum -y remove kbd

yum -y remove NetworkManager
yum -y remove plymouth
yum -y remove uboot-tools

#Grab any updates and cleanup
yum -y update yum
yum -y update
yum -y clean all

#Install ztps-related related packages
yum -y install python-devel
yum -y install gcc make gcc-c++
yum -y install xz-libs
yum -y install tar
yum -y install wget
yum -y install git
yum -y install net-tools
yum -y install httpd
yum -y install httpd-devel
yum -y install dhcp
yum -y install bind
yum -y install ejabberd

#systemctl stop NetworkManager.service
#systemctl disable NetworkManager.service
#systemctl start network.service
#systemctl enable network.service

#Create a place for packer to upload service configurations
#mkdir /tmp/packer


#Install Python 2.7.6
#cd /tmp
#wget http://www.python.org/ftp/python/2.7.6/Python-2.7.6.tar.xz
#xz -d Python-2.7.6.tar.xz
#tar -xvf Python-2.7.6.tar
#cd Python-2.7.6
#./configure --prefix=/usr/local
#make
#make altinstall


######################################
#INSTALL PIP
######################################
cd /tmp
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py

#Install Virtualenv
pip install virtualenv


######################################
# CONFIGURE APACHE AND INSTALL MODWSGI
######################################
cd /tmp
wget https://github.com/GrahamDumpleton/mod_wsgi/archive/4.1.3.tar.gz
tar xvfz 4.1.3.tar.gz
cd mod_wsgi-4.1.3
./configure
make
make install


######################################
# INSTALL ZTPSERVER
######################################
#mkdir /etc
cd /home/ztpsadmin

#clone from GitHub
git clone https://github.com/arista-eosplus/ztpserver.git -b release-1.0
cd ztpserver

#build/install
python setup.py build
python setup.py install