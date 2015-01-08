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

import os
import shutil

from glob import glob
from ztpserver import config

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = ['ztpserver']

conf_path = config.CONF_PATH
install_path = config.INSTALL_PATH

if os.environ.get('READTHEDOCS'):
    print 'Customizing install for ReadTheDocs.org build servers...'
    conf_path = '.' + conf_path
    install_path = '.' +  install_path
    from subprocess import call
    call(['docs/setup_rtd_files.sh'])
    packages.append('client')
    packages.append('actions')

install_requirements = open('requirements.txt').read().split('\n')
version = open('VERSION').read().split()[0].strip()

setup(
    name='ztpserver',
    version=version,
    description = 'ZTP Server for EOS',
    author='Arista Networks',
    author_email='eosplus-dev@arista.com',
    url='https://github.com/arista-eosplus/ztpserver',
    download_url='https://github.com/arista-eosplus/ztpserver/tarball/v%s' % \
                  version,
    license='BSD-3',
    install_requires=install_requirements,
    packages=packages,
    scripts=glob('bin/*'),
    data_files=[
        ('%s/nodes' % install_path, []),
        ('%s/definitions' % install_path, []),
        ('%s/files' % install_path, []),
        ('%s/resources' % install_path, []),
        (conf_path, glob('conf/ztpserver.conf')),
        (conf_path, glob('conf/ztpserver.wsgi')),
        (conf_path, ['VERSION']),
        ('%s/bootstrap' % install_path, glob('client/bootstrap')),
        ('%s/bootstrap' % install_path, glob('conf/bootstrap.conf')),
        ('%s/actions' % install_path, glob('actions/*')),
        ('%s' % install_path, glob('conf/neighbordb')),

        # 4.12.x support
        ('%s/files/lib' % install_path, glob('client/lib/requests-2.3.0.tar.gz')),
    ]
)

# Hide VERSION file
shutil.rmtree(config.VERSION_FILE_PATH, ignore_errors=True)
shutil.move('%s/VERSION' % conf_path, config.VERSION_FILE_PATH)
