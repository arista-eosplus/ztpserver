#!/usr/bin/make
# WARN: gmake syntax
########################################################
# Makefile for ztpserver
#
# useful targets:
#   make sdist -- builds a source distribution
#   make pyflakes, make pep8 -- source code checks
#   make tests -- run the tests
#   make clean -- cleans distutils

########################################################
# variable section

NAME = "ztpserver"
PYTHON = python

VERSION := $(shell cat VERSION)

########################################################

all: clean python

pep8:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests"
	@echo "#############################################"
	-pep8 -r --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225,E261,E241 ztpserver/ bin/
	-pep8 -r --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225,E261,E241 --filename "*" client/

pyflakes:
	pyflakes ztpserver/* bin/*

clean:
	@echo "Cleaning up distutils stuff"
	rm -rf build
	rm -rf dist
	rm -rf MANIFEST
	@echo "Cleaning up byte compiled python stuff"
	find . -type f -regex ".*\.py[co]$$" -delete

tests: clean
	$(PYTHON)  -m unittest discover ./test -v

python:
	$(PYTHON) setup.py build

install:
	$(PYTHON) setup.py install

sdist: clean
	$(PYTHON) setup.py sdist -t MANIFEST.in



