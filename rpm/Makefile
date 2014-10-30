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

PACKAGE = "ztpserver"
RPMSPECDIR = .
RPMSPEC = $(RPMSPECDIR)/$(PACKAGE).spec
HTTPDCONF = $(RPMSPECDIR)/$(PACKAGE)-wsgi.conf

# VERSION file provides one place to update the software version
VERSION := $(shell cat VERSION)

# Spec files cannot contain extraneous strings - so just extract numbered release
SPECVERSION := $(shell sed -n 's/.*\([0-9]\.[0-9]\.[0-9]\).*/\1/p' VERSION)
RPMRELEASE = 1


# RPM build parameters
#ARCH = noarch

RPMBUILD = rpmbuild --define "_topdir %(pwd)/rpm-build" \
        --define "_builddir %{_topdir}" \
        --define "_rpmdir %(pwd)/rpms" \
        --define "_srcrpmdir %{_rpmdir}" \
        --define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}%%{?dist}.rpm" \
        --define "_sourcedir  %(pwd)/dist/"

########################################################

all: rpm

clean:
	@echo "---------------------------------------------"
	@echo "Cleaning up"
	@echo "---------------------------------------------"
	rm -rf dist/ build/ rpm-build/ rpms/ *~

sdist:
	mkdir -p dist/
	tar --directory=.. -czf dist/${PACKAGE}.tgz ${PACKAGE} --exclude=dist --exclude=rpm-build --exclude=rpms
	cp ${HTTPDCONF} dist/${HTTPDCONF}
	@sed -i.bak 's/^Version:.*/Version: $(SPECVERSION)/g' $(RPMSPEC)
	@sed -i.bak 's/^Release:.*/Release: $(RPMRELEASE)%{?dist}/g' $(RPMSPEC)

prep_rpmbuild: sdist
	mkdir -p rpm-build
	mkdir -p rpms

rpm: prep_rpmbuild
	${RPMBUILD} -ba ${PACKAGE}.spec

srpm: prep_rpmbuild
	${RPMBUILD} -bs ${PACKAGE}.spec
