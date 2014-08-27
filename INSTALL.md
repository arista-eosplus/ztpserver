# INSTALL for ZTP Server


### Ubuntu 12.04.1 LTS

`````
$ git clone https://github.com/arista-eosplus/ztpserver.git
$ cd ztpserver

$ sudo apt-get install python-setuptools python-dev
$ sudo easy_install routes
$ sudo easy_install webob
$ sudo easy_install PyYaml

$ sudo make install

$ ztps
``````