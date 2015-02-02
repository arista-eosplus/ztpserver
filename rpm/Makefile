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
SPECVERSION := $(shell sed -n 's/.*\([0-9]\.[0-9]\.[0-9]\).*/\1/p' ../VERSION)
RPMRELEASE = 3


# RPM build parameters
#ARCH = noarch

RPMBUILD = rpmbuild --define "_topdir %(pwd)/rpmbuild" \
        --define "_builddir %{_topdir}" \
        --define "_rpmdir %(pwd)/rpms" \
        --define "_srcrpmdir %{_rpmdir}" \
        --define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.rpm" \
        --define "_sourcedir  %(pwd)/dist/"

########################################################

all: rpm

clean:
	@echo "---------------------------------------------"
	@echo "Cleaning up"
	@echo "---------------------------------------------"
	rm -rf dist/ build/ rpmbuild/ rpms/ *~ ../$(PACKAGE).spec

sdist:
	@cp $(RPMSPEC) ../$(PACKAGE).spec
	@sed -i -e 's/^Version:.*/Version: $(SPECVERSION)/g' ../$(PACKAGE).spec
	@sed -i -e 's/^Release:.*/Release: $(RPMRELEASE)%{?dist}/g' ../$(PACKAGE).spec
	mkdir -p dist/
	@ln -s ../../../${PACKAGE} dist/${PACKAGE}-${SPECVERSION}
	tar --directory=dist --dereference -czf dist/${PACKAGE}-${SPECVERSION}.tgz ${PACKAGE}-${SPECVERSION} --exclude=rpm --exclude=.git --exclude=.gitignore --exclude=ztpserver.egg-info
	@rm dist/${PACKAGE}-${SPECVERSION}
	cp ${HTTPDCONF} dist/${HTTPDCONF}

prep_rpmbuild: sdist
	mkdir -p rpmbuild
	mkdir -p rpms

rpm: prep_rpmbuild
	${RPMBUILD} -ba ../${PACKAGE}.spec

srpm: prep_rpmbuild
	${RPMBUILD} -bs ../${PACKAGE}.spec
