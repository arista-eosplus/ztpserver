#!/usr/bin/make
# WARN: gmake syntax
########################################################
# Makefile for ZTPServer
#
# useful targets:
#   make clean ----- cleans distutils
#   make rpm  ------ produce RPMs
#   make srpm ------ produce Source RPMs
#
########################################################
# variable section

SHELL = /bin/sh

PACKAGE = ztpserver
RPMSPECDIR = .
RPMSPEC = $(RPMSPECDIR)/$(PACKAGE).spec
HTTPDCONF = $(RPMSPECDIR)/$(PACKAGE)-wsgi.conf

# VERSION file provides one place to update the software version
VERSION := $(shell cat ../VERSION)

# Spec files cannot contain extraneous strings - so just extract numbered release
SPECVERSION := $(shell sed -n 's/[^0-9\.]*\([0-9\.]*\)[^0-9\.]*/\1/p' ../VERSION)
RPMRELEASE = 1


# RPM build parameters
#ARCH = noarch

RPMBUILD = rpmbuild --define "_topdir %(pwd)/rpmbuild" \
        --define "_builddir %{_topdir}" \
        --define "_rpmdir %(pwd)/rpms" \
        --define "_srcrpmdir %{_rpmdir}" \
        --define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.rpm" \
        --define "_sourcedir  %(pwd)/../dist/"

########################################################

all: rpm

clean:
	@echo "---------------------------------------------"
	@echo "Cleaning up"
	@echo "---------------------------------------------"
	rm -rf dist/ build/ rpmbuild/ rpms/ *~ ../$(PACKAGE).spec

../ztpserver.spec: ../VERSION
	@cp $(RPMSPEC) ../$(PACKAGE).spec
	@sed -i -e 's/^Version:.*/Version: $(SPECVERSION)/g' ../$(PACKAGE).spec
	@sed -i -e 's/^Release:.*/Release: $(RPMRELEASE)%{?dist}/g' ../$(PACKAGE).spec

rpm:
	$(MAKE) -C .. rpm

srpm:
	$(MAKE) -C .. srpm

rpm-pkg: ../${PACKAGE}.spec
	${RPMBUILD} -ba ../${PACKAGE}.spec

srpm-pkg: ../${PACKAGE}.spec
	${RPMBUILD} -bs ../${PACKAGE}.spec
