#!/bin/bash

if [ $# -lt 1 ]; then
  echo "Usage: source env-setup envpath"
  return
fi;

if [ ! -d .env ]; then
  echo Installing virtualenv into $1
  virtualenv -q $1

  echo Switching to virtualenv
  source $1/bin/activate
  
  echo Installing Python packages via PIP
  pip install -q -r requirements.txt
else
  echo Switching to virtualenv
  source $1/bin/activate
fi;

if [ ! -d .env/etc ]; then
  echo Creating etc directory
  mkdir -p $1/etc
  cp conf/ztpserver.conf $1/etc
fi;

if [ ! -d .env/filestore ]; then
  echo Creating filestore directories
  mkdir -p $1/filestore/nodes
  mkdir -p $1/filestore/definitions
  mkdir -p $1/filestore/packages
  mkdir -p $1/filestore/files
fi;

echo Setting environment variables
export PYTHONPATH=$PWD
export PATH=$PWD/bin:$PATH

unset ZTPS_CONFIG
export ZTPS_CONFIG=$PWD/$1/etc/ztpserver.conf

echo
echo PTYHONPATH=$PYTHONPATH
echo PATH=$PATH
echo ZTPS_CONFIG=$ZTPS_CONFIG

echo
echo Done! 
echo