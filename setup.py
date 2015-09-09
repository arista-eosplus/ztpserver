# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# Copyright (c) 2015, Arista Networks, Inc.
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
import sys

from glob import glob
from ztpserver import config

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def install():
    if "install" in sys.argv:
        return True
    else:
        return False

def join_url(x, y):
    return '/' + '/'.join([z for z in x.split('/') + y.split('/') if z])

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

conf_path = config.CONF_PATH
install_path = config.INSTALL_PATH

if install() and os.environ.get('ZTPS_INSTALL_PREFIX'):
    print "Customizing install for VirtualEnv install with RPM"
    conf_path = join_url(os.environ.get('ZTPS_INSTALL_PREFIX'), config.CONF_PATH)
    install_path = join_url(os.environ.get('ZTPS_INSTALL_PREFIX'), config.INSTALL_PATH)

packages = ['ztpserver']
if install() and os.environ.get('READTHEDOCS'):
    print 'Customizing install for ReadTheDocs.org build servers...'
    conf_path = '.' + conf_path
    install_path = '.' +  install_path
    os.environ['ZTPS_INSTALL_ROOT'] = '.'
    from subprocess import call
    call(['docs/setup_rtd_files.sh'])
    packages.append('client')
    packages.append('actions')
    packages.append('plugins')

install_requirements = None
version = None

install_requirements = open('requirements.txt').read().split('\n')
install_requirements = [x.strip() for x in install_requirements
                        if x.strip() and
                        'dev only' not in x]
version = open('VERSION').read().split()[0].strip()

data_files = []
# configuration folders are not cleared on upgrade/downgrade
for folder in ['nodes', 'definitions', 'files', 'resources',
               'bootstrap', 'config-handlers']:
    path = '%s/%s' % (install_path, folder)
    if install() and not os.path.isdir(path):
        if os.path.exists(path):
            os.remove(path)
        data_files += [(path, [])]

for (filename, dst, src) in [('neighbordb',
                              install_path,
                              'conf/neighbordb'),
                             ('bootstrap.conf',
                              '%s/bootstrap' % install_path,
                              'conf/bootstrap.conf'),
                             ('ztpserver.conf',
                              conf_path,
                              'conf/ztpserver.conf'),
                             ('ztpserver.wsgi',
                              conf_path,
                              'conf/ztpserver.wsgi')]:
    file_path = '%s/%s' % (dst, filename)
    if install() and os.path.exists(file_path):
        if os.path.isdir(file_path):
            shutil.rmtree(file_path,
                          ignore_errors=True)
        else:
            # do this manually
            shutil.copy(src, file_path + '.new')
            continue

    data_files += [(dst, glob(src))]

# bootstrap file, libraries, VERSION, plugins and actions are
# always overwritten
file_list = [('bootstrap', '%s/bootstrap' % install_path,
              'client/bootstrap')]
for filename in glob('actions/*'):
    file_list += [(filename.split('/')[-1],
                   '%s/actions' % install_path,
                   filename)]
for filename in glob('plugins/*'):
    file_list += [(filename.split('/')[-1],
                   '%s/plugins' % install_path,
                   filename)]
for filename in glob('client/lib/*'):
    file_list += [(filename.split('/')[-1],
                   '%s/files/lib' % install_path,
                   filename)]
for (filename, dst, src) in file_list:
    file_path = '%s/%s' % (dst, filename)
    if install() and os.path.exists(file_path) and \
            os.path.isdir(file_path):
        shutil.rmtree(file_path,
                      ignore_errors=True)
    data_files += [(dst, glob(src))]

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
    data_files=data_files
)

# hidden version file
if install():
    custom_path = os.environ.get('ZTPS_INSTALL_ROOT')
    if custom_path:
        version_file =  join_url(custom_path, config.VERSION_FILE_PATH)[1:]
    else:
        version_file =  config.VERSION_FILE_PATH
    ensure_dir(version_file)
    shutil.copy('VERSION', version_file)
