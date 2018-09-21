FROM centos:7

MAINTAINER Cheyne Womble <cwomble@arista.com>

RUN yum -y --setopt="tsflags=nodocs" update && \
	yum -y --setopt="tsflags=nodocs" install epel-release mock rpmdevtools rpm-sign rpmlint make && \
	yum clean all && \
	rm -rf /var/cache/yum/

#RUN useradd builder -G mock -M -d /rpmbuild
#Configure users
RUN useradd -u 1000 -G mock builder

# create mock cache on external volume to speed up build
RUN install -g mock -m 2775 -d /rpmbuild/cache/mock
RUN echo "config_opts['cache_topdir'] = '/rpmbuild/cache/mock'" >> /etc/mock/site-defaults.cfg
