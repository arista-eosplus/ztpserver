# docker build -t ztpserver .
# docker run -P ztpserver
# docker run -i -t --rm -p 80:80 nginx
#
FROM python:2

LABEL version="0.1"
LABEL maintainer="eosplus-dev@arista.com"

WORKDIR /src/ztpserver

# ADD myscript.py /
# RUN pip install ztpserver

COPY . .
# COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python setup.py install

VOLUME ["/usr/share/ztpserver", "/etc/ztpserver"]

# RUN groupadd -r ztpsadmin && useradd --no-log-init -r -g ztpsadmin ztpsadmin

# EXPOSE TCP/8080 TCP/80

WORKDIR /usr/share/ztpserver
# CMD [ "python", "./myscript.py" ]
# CMD sh

# docker run -p 8080:8080 ztpserver [-d]
ENTRYPOINT /usr/local/bin/ztps
