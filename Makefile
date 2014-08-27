#!/usr/bin/make
# WARN: gmake syntax
########################################################
# Makefile for ztpserver
#
# useful targets:
#   make sdist -- builds a source distribution
#   make pylint -- source code checks
#   make tests -- run the tests
#   make test_server -- run all server tests (including neighbordb)
#   make test_server TESTNAME=<name of test>
#   make test_client -- run client tests
#   make test_client TESTNAME=<name of test>
#   make test_actions -- run action tests only
#   make test_actions TESTNAME=<name of test>
#   make test_neighbordb -- run neighbordb tests only
#   make clean -- cleans distutils
#
########################################################
# variable section

NAME = "ztpserver"
PYTHON = python
TESTNAME = discover

VERSION := $(shell cat VERSION)

########################################################

all: clean python

pylint:
	find ./ztpserver -name \*.py | xargs pylint --rcfile .pylintrc
	find ./test -name \*.py | xargs pylint --rcfile .pylintrc
	find ./actions -name \* -xtype f | xargs pylint --rcfile .pylintrc
	find ./client -name bootstrap | xargs pylint --rcfile .pylintrc

clean:
	@echo "Cleaning up distutils stuff"
	rm -rf build
	rm -rf dist
	rm -rf ztps
	rm -rf MANIFEST
	@echo "Cleaning up byte compiled python stuff"
	find . -type f -regex ".*\.py[co]$$" -delete

test_neighbordb: clean
	PYTHONPATH=./ $(PYTHON)  ./test/server/test_neighbordb.py

test_client: clean
ifeq ($(TESTNAME),discover)
	$(PYTHON)  -m unittest discover test/client -v
else
	$(PYTHON)  test/client/$(TESTNAME) -v
endif

test_actions: clean
ifeq ($(TESTNAME),discover)
	$(PYTHON)  -m unittest discover test/actions -v
else
	$(PYTHON)  test/actions/$(TESTNAME) -v
endif

test_server: clean
ifeq ($(TESTNAME),discover)
	$(PYTHON)  -m unittest discover test/server -v
else
	$(PYTHON)  test/server/$(TESTNAME) -v
endif

tests: clean test_server test_client test_actions

python:
	$(PYTHON) setup.py build

install:
	$(PYTHON) setup.py install

sdist: clean
	$(PYTHON) setup.py sdist -t MANIFEST.in
