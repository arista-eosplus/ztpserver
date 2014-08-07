# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# Copyright (c) 2014, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from glob import glob

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from ztpserver import __version__, __author__

CONF_PATH = '/etc/ztpserver'
INSTALL_PATH = '/usr/share/ztpserver'
INSTALL_REQUIREMENTS = open('requirements.txt').read().split('\n')

setup(
    name='ztpserver',
    version=__version__,
    description = 'ZTP Server for EOS',
    author=__author__,
    author_email='eosplus@aristanetworks.com',
    url='https://github.com/arista-eosplus/ztpserver',
    download_url='https://github.com/arista-eosplus/ztpserver/tarball/v1.0.0',
    license='BSD-3',
    install_requires=INSTALL_REQUIREMENTS,
    packages=['ztpserver'],
    scripts=glob('bin/*'),
    data_files=[
        (CONF_PATH, ['conf/ztpserver.conf']),
        ('%s/bootstrap' % INSTALL_PATH, glob('client/bootstrap')),
        ('%s/actions' % INSTALL_PATH, glob('actions/*')),
        ('%s/nodes' % INSTALL_PATH, []),
        ('%s/definitions' % INSTALL_PATH, []),
        ('%s/files' % INSTALL_PATH, []),
        ('%s/resources' % INSTALL_PATH, []),
        ('%s' % INSTALL_PATH, ['conf/neighbordb']),

        # 4.12.x support
        ('%s/files/lib' % INSTALL_PATH, ['client/lib/requests-2.3.0.tar.gz']),
    ]
)
