#################################
# Application specific settings #
#################################
%define app_name    ztpserver
%define app_version 1.2.0
%define app_summary "Arista Zero Touch Provisioning Server for Arista EOS Devices."
%define app_virtualenv_dir  opt/ztpsrv_env
%define app_user    ztpserver

#### This part is used to directly fetch sources from within the build section 
#### (handled externally when built w/ jenkins):
%define app_url      https://github.com/arista-eosplus/ztpserver.git
%define httpd_dir    opt/rh/httpd24/root/etc/httpd/conf.d

Name:    %{app_name}
Version: %{app_version}
Release: 1%{?dist}
Summary: %{app_summary}

Group:    Network
License:  NonPublic
URL:      %{app_url}
#Source0: %{name}.init
Source1:  %{name}-wsgi.conf

### Don't allow rpmbuild to modify dependencies 
AutoReqProv: no

BuildRequires: python-virtualenv, python27, python27-python-virtualenv, mock, git
Requires: python-virtualenv, python27, python27-python-virtualenv, dhcp, httpd24, python27-mod_wsgi

BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-%{id -un}

%description
ZTPServer provides a bootstrap environment for Arista EOS based products.
ZTPserver interacts with the ZeroTouch Provisioning (ZTP) mode of Arista EOS.
The default ZTP start up mode triggers an unprovisioned Arista EOS nodes to
enter a bootstrap ready state if a valid configuration file is not already
present on the internal flash storage.

ZTPServer provides a number of configurable bootstrap operation workflows that
extend beyond simply loading an configuration and boot image. It provides the
ability to define the target node through the introduction of definitions and
templates that call pre-built actions and statically defined or dynamically
generated attributes. The attributes and actions can also be extended to provide
custom functionality that are specific to a given implementation. ZTPServer also
provides a topology validation engine with a simple syntax to express LLDP 
neighbor adjacencies. It is written mostly in Python and leverages standard 
protocols like DHCP and DHCP options for boot functions, HTTP for 
bi-directional transport, and XMPP and syslog for logging. Most of the files 
that the user interacts with are YAML based.

%prep
%setup -q -c -T -n %{name}-%{version}-%{release}

# prepare virtualenv w/ python27 for build of ztpserver source
export X_SCLS=python27
source /opt/rh/python27/enable
virtualenv-2.7 -v --system-site-packages %{app_virtualenv_dir}
source %{app_virtualenv_dir}/bin/activate

cd %{app_virtualenv_dir}
pip install setuptools --upgrade
git clone %{app_url} ztpserver-gitsrc
cd ztpserver-gitsrc

### For testing purposes just checkout develop
#git checkout v%{version}
git checkout develop


#%build
python setup.py build


%install
# export virtualenv vars again and activate it (apparently \install macro has its own shell/env):
export X_SCLS=python27
source /opt/rh/python27/enable
source %{app_virtualenv_dir}/bin/activate
cd %{app_virtualenv_dir}/ztpserver-gitsrc
python setup.py install

# clean-up gitsrc dir after install:
cd ..
rm -rf ztpserver-gitsrc

# install everything into RPM_BUILD_ROOT:
cd $RPM_BUILD_DIR/%{name}-%{version}-%{release}
mkdir -p $RPM_BUILD_ROOT/{usr/share,etc}
mkdir -p $RPM_BUILD_ROOT/%{app_virtualenv_dir}
cp -rp %{app_virtualenv_dir}/* $RPM_BUILD_ROOT/%{app_virtualenv_dir}/
mkdir -p $RPM_BUILD_ROOT/%{httpd_dir}
cp -rp %{SOURCE1} $RPM_BUILD_ROOT/%{httpd_dir}/%{name}-wsgi.conf

# fix shebangs before packaging the files:
grep -sHE '^#!/builddir/build/BUILD/%{name}-%{version}-%{release}/%{app_virtualenv_dir}/bin/python' $RPM_BUILD_ROOT/%{app_virtualenv_dir}/bin/* -r | awk -F: '{ print $1 }' | uniq | while read line; do sed -i 's@^#\!/builddir/build/BUILD/%{name}-%{version}-%{release}/%{app_virtualenv_dir}/bin/python@#\!/%{app_virtualenv_dir}/bin/python@' $line; done

grep -sHE '^VIRTUAL_ENV=\"/builddir/build/BUILD/%{name}-%{version}-%{release}/%{app_virtualenv_dir}\"' $RPM_BUILD_ROOT/%{app_virtualenv_dir}/bin/* -r | awk -F: '{ print $1 }' | uniq | while read line; do sed -i 's@^VIRTUAL_ENV=\"/builddir/build/BUILD/%{name}-%{version}-%{release}/%{app_virtualenv_dir}\"@VIRTUAL_ENV=\"/%{app_virtualenv_dir}\"@' $line; done


%pre
getent group %{app_user} > /dev/null || groupadd -r %{app_user}
getent passwd %{app_user} > /dev/null || \
  useradd -m -g %{app_user} -d /%{app_virtualenv_dir} -s /bin/bash \
  -c "%{name} - Server" %{app_user}


%posttrans


%post
ln -s /%{app_virtualenv_dir}/usr/share/ztpserver /usr/share/
ln -s /%{app_virtualenv_dir}/etc/ztpserver /etc/
chcon -Rv --type=httpd_sys_content_t /%{app_virtualenv_dir}/usr/share/ztpserver
#/sbin/service httpd24-httpd restart

%preun
# $1 --> if 0, then it is a deinstall
# $1 --> if 1, then it is an upgrade


%postun
# $1 --> if 0, then it is a deinstall
# $1 --> if 1, then it is an upgrade
#if [ $1 -eq 0 ]; then
#    userdel -r %{app_user}
#    #groupdel %{app_user}
#fi
# remove symlink relics:
rm /usr/share/ztpserver
rm /etc/ztpserver


%files
# all the files to be included in this RPM:
%defattr(-,root,root,)
%config(noreplace) /%{app_virtualenv_dir}/etc/ztpserver/ztpserver.conf
#%attr(0755,root,root) %{_initddir}/%{name}
%attr(0755,%{name},root) /%{app_virtualenv_dir}
%attr(0755,%{name},root) /%{httpd_dir}/%{name}-wsgi.conf

%clean
rm -rf $RPM_BUILD_ROOT


%changelog
* Tue Oct 28 2014 Arista Networks <eosplus-dev@arista.com> - 1.2.0-1
- Remove standalone ZTPServer functions from SPEC
- Remove ztpserver.init script
- Add dependencies for Software Collections httpd24 and python27-mod_wsgi
- Add SOURCE ztpserver-wsgi.conf which is placed in httpd24 conf.d directory
- Modify SELinux policy so that httpd can write to /usr/share/ztpserver

* Fri Oct 10 2014 tzhnape1 <peter.najdenik@swisscom.com> - 1.1.0-1
- Release 1 of ZTPserver RPM using virtualenv and python 27 from RH SCL.
TODO:
- sync git source from script and put all sources into tar archive
- source archive via prep
- [done] fix env declaration in ztps script in \install section before cleaning up --> see shebang fixes
- [done] cleanup specfile variables and put definitions for http proxy server in header
- [done] source scl env via enable script instead of declaring/exporting env variables manually
- [done] fix post install and uninstall sections
- [done] write changelog
- refactor spec/rpm part for integration with jenkings & puppet - "init.sh"
- handle selinux if necessary (virtualenv dir, sysconfdir, etc.)

* Wed Oct 8 2014 tzhnape1 <peter.najdenik@swisscom.com>
- Fixed sed script to change environment path in activate script of vritualenv, which caused the rpm not to build anymore
- Some cleanup and recoding of specfile done.

* Mon Oct 6 2014 tzhnape1 <peter.najdenik@swisscom.com>
- Changed the export of env variables for python 2.7 scl env to source the 'enable' script which does the same.
- Fixed shebangs with path variables in ztps set during build in setup/install section (buildroot pfad was used due to the build env being active while building)
- Fixed cleanup missing for symlinks at removal of the package

* Fri Sep 26 2014 tzhnape1 <peter.najdenik@swisscom.com>
- Fixed \install section issue with virtualenv/shell env settings getting lost
- Tweaked packaging files list

* Wed Sep 3 2014 tzhnape1 <peter.najdenik@swisscom.com>
- Fixed build/install section so it properly works with python-virtualenv
- Fixed install paths and files list
- Added symlinks to systemconfdir and usrdir for virtualenv for ease of access
- Fixed/added GitHub source (Gitlab requires authentication)

* Wed Aug 27 2014 tzhnape1 <peter.najdenik@swisscom.com>
- Initial release/build of ztpserver

