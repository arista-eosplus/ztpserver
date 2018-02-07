# docker build -t ztpserver .
# docker run -P ztpserver
# docker run -i -t --rm -p 80:80 nginx
#
FROM python:2

LABEL version="0.1"
LABEL maintainer="eosplus-dev@arista.com"

WORKDIR /src/ztpserver

# COPY . .
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt
COPY dist/ztpserver-*.tar.gz ./
RUN pip install --no-cache-dir  ztpserver-*.tar.gz

VOLUME ["/usr/share/ztpserver", "/etc/ztpserver"]

# RUN groupadd -r ztpsadmin && useradd --no-log-init -r -g ztpsadmin ztpsadmin

EXPOSE 8080/TCP

# WORKDIR /usr/share/ztpserver
# CMD [ "python", "./myscript.py" ]
# CMD sh

# docker run -p 8080:8080 ztpserver [-d]
ENTRYPOINT /usr/local/bin/ztps
