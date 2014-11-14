#################################
# Application specific settings #
#################################
%global app_summary         "Arista Zero Touch Provisioning Server for Arista EOS Devices."
%global app_url             https://github.com/arista-eosplus/ztpserver/
%global app_user            ztpserver
%{!?python2_sitelib: %global python2_sitelib /usr/lib/python2.7/site-packages }

%if 0%{?rhel} == 6
%global httpd_dir           /opt/rh/httpd24/root/etc/httpd/conf.d
%global app_virtualenv_dir  /opt/ztpsrv_env
%global basedatadir         %{_datadir}
%global basesysconfdir      %{_sysconfdir}
%global python2_sitelib     %{app_virtualenv_dir}/lib/python2.7/site-packages
%global python2_sitearch    /lib64/python2.7/site-packages
%else
%global httpd_dir           %{_sysconfdir}/httpd/conf.d
%endif

# We don't need the -debug package
%global debug_package %{nil}

Name:    ztpserver
Version: BLANK
Release: 2%{?dist}
Summary: %{app_summary}

Group:    Network
License:  BSD-3
URL:      %{app_url}
Source0:  %{name}-%{version}.tgz
Source1:  %{name}-wsgi.conf

### Don't allow rpmbuild to modify dependencies 
AutoReqProv: no

BuildRequires: python-pip

%if 0%{?rhel} == 6
BuildRequires: python27
BuildRequires: python-virtualenv
BuildRequires: python27-python-virtualenv
BuildRequires: python27-python-setuptools
%else
BuildRequires: python >= 2.7
BuildRequires: python < 3
BuildRequires: python-setuptools
%endif

%if 0%{?rhel} == 6
Requires: python27
Requires: python-virtualenv
Requires: python27-python-virtualenv
Requires: httpd24
Requires: python27-mod_wsgi
%else
Requires: python >= 2.7
Requires: python < 3
Requires: httpd
Requires: mod_wsgi
%endif

Requires(pre): shadow-utils

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
%setup

%build
%if 0%{?rhel} == 6
## Prepare virtualenv w/ python27 for build of ztpserver source
export X_SCLS=python27
source /opt/rh/python27/enable
virtualenv-2.7 -v --system-site-packages $RPM_BUILD_DIR%{app_virtualenv_dir}
source $RPM_BUILD_DIR%{app_virtualenv_dir}/bin/activate
%endif

python setup.py build


%install
%if 0%{?rhel} == 6
## Set into the virtualenv w/ python27
export X_SCLS=python27
source /opt/rh/python27/enable
source $RPM_BUILD_DIR%{app_virtualenv_dir}/bin/activate

# Move necessary file from RPM_BUILD_DIR into RPM_BUILD_ROOT:
%{__install} -d $RPM_BUILD_ROOT%{app_virtualenv_dir}
cp -rp $RPM_BUILD_DIR%{app_virtualenv_dir}/* $RPM_BUILD_ROOT%{app_virtualenv_dir}
%endif

# Allow us to install libs in to RPM_BUILD_ROOT
# Force some paths for install to handle the virtual_env case for RHEL
%{__install} -d $RPM_BUILD_ROOT%{python2_sitelib}
PYTHONPATH=$RPM_BUILD_ROOT%{python2_sitelib}:${PYTHONPATH} \
python setup.py install --root=$RPM_BUILD_ROOT  --install-scripts=%{_bindir} \
--install-lib=%{python2_sitelib}

%{__install} -pD %{SOURCE1} $RPM_BUILD_ROOT%{httpd_dir}/%{name}-wsgi.conf


%pre
getent group %{app_user} > /dev/null || groupadd -r %{app_user}
getent passwd %{app_user} > /dev/null || \
  useradd -m -g %{app_user} -d %{_datadir}/ztpserver/ -s /bin/false \
  -c "%{name} - Server" %{app_user}
exit 0

%posttrans


%post
# Ensure the server can read/write the necessary files.
# ZTPServer operators may be put in to this group to allow them to configure the service
chown -R %{app_user}:%{app_user} %{_datadir}/ztpserver
chmod -R ug+rw %{_datadir}/ztpserver
chcon -Rv --type=httpd_sys_content_t %{_datadir}/ztpserver

%preun
# $1 --> if 0, then it is a deinstall
# $1 --> if 1, then it is an upgrade


%postun
# $1 --> if 0, then it is a deinstall
# $1 --> if 1, then it is an upgrade


%files
# all the files to be included in this RPM:
%defattr(-,root,root,)
%if 0%{?rhel} == 6
%{app_virtualenv_dir}
%else
%{python2_sitelib}/%{name}
%{python2_sitelib}/%{name}-%{version}*.egg-info
%endif

%{_bindir}/ztps

%dir %{_sysconfdir}/ztpserver
%config(noreplace) %{_sysconfdir}/ztpserver/ztpserver.conf
%config(noreplace) %{_sysconfdir}/ztpserver/ztpserver.wsgi
%config(noreplace) %{httpd_dir}/%{name}-wsgi.conf

%defattr(0775,%{app_user},%{app_user},)
%dir %{_datadir}/ztpserver
%dir %{_datadir}/ztpserver/actions
%dir %{_datadir}/ztpserver/bootstrap
%dir %{_datadir}/ztpserver/definitions
%dir %{_datadir}/ztpserver/files
%dir %{_datadir}/ztpserver/files/lib
%dir %{_datadir}/ztpserver/nodes
%dir %{_datadir}/ztpserver/resources

%defattr(0665,%{app_user},%{app_user},)
%{_datadir}/ztpserver/files/lib/*
%config(noreplace) %{_datadir}/ztpserver/actions/*
%config(noreplace) %{_datadir}/ztpserver/bootstrap/*
%config(noreplace) %{_datadir}/ztpserver/neighbordb

%clean
rm -rf $RPM_BUILD_ROOT


%changelog
* Mon Nov 03 2014 Arista Networks <eosplus-dev@arista.com> - 1.2.0-2
- Add logic to work with virtualenv installs versus standard installs
- For virtualenv installs, all python dependencies will be installed
- For standard installs, only ztpserver egg and /usr/share/ztpserver files are included (as well as config in /etc/ztpserver and /usr/bin/ztps)

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

* Fri Nov 14 2014 Jere Julian <jere@arista.com>
- Increase utilization of built-in macros
- Replace %define (runtime expansion) with %global (immediate)
- Add app_url
- Disable the -debug package fro being built
- Source0 now has version-info and unpacks in to a versioned dir
- Remove manual override of BuildRoot
- Move python setup.py install to %install
- Force some install path info for python setup so it properly places files, both in and out of a virtualenv
- Replace "cp -rp and mkdir -p" with %{__install}
- Consolidate useradd code in %pre and change the user/s HOME
- Remove symlinks on virtualenv systems (rhel6) as paths are fixed
- Remove userdel from %preun as we can't guarantee other file ownership
- Specifically call out directories, config files, and permissions in %files
