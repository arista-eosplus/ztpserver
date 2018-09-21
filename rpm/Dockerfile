FROM centos:7

MAINTAINER Cheyne Womble <cwomble@arista.com>

RUN yum -y install epel-release && yum clean all
RUN yum -y install mock rpmdevtools rpm-sign rpmlint && yum clean all
RUN useradd builder -G mock -M -d /rpmbuild
RUN echo "config_opts['cache_topdir'] = '/rpmbuild/cache'" >> /etc/mock/site-defaults.cfg
