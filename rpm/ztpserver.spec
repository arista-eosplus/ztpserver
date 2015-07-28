#################################
# Application specific settings #
#################################
%global app_summary         "Arista Zero Touch Provisioning Server for Arista EOS Devices."
%global app_url             https://github.com/arista-eosplus/ztpserver/
%global app_user            ztpserver

%if 0%{?rhel} == 6
%global httpd_dir           /opt/rh/httpd24/root/etc/httpd/conf.d
%global app_virtualenv_dir  /opt/ztpsrv_env
%global python2_sitelib     %{app_virtualenv_dir}/lib/python2.7/site-packages
%global python2_sitearch    %{app_virtualenv_dir}/lib64/python2.7
%global _datadir            %{app_virtualenv_dir}%{_datadir}
%global _sysconfdir         %{app_virtualenv_dir}%{_sysconfdir}
%global _bindir             %{app_virtualenv_dir}%{_bindir}
%global apphomedir          %{app_virtualenv_dir}
%global ztps_data_root      %{app_virtualenv_dir}/usr/share/ztpserver
%else
%global httpd_dir           %{_sysconfdir}/httpd/conf.d
%global ztps_data_root      /usr/share/ztpserver
%global apphomedir          %{_datadir}/ztpserver
%endif

# We don't need the -debug package
%global debug_package %{nil}

Name:    ztpserver
Version: BLANK
Release: 1%{?dist}
Summary: %{app_summary}

Group:    Applications/Communications
License:  BSD-3
URL:      %{app_url}
Source0:  %{name}-%{version}.tar.gz

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
BuildRequires: python2-devel
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
%setup -q

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
export ZTPS_INSTALL_PREFIX=%{app_virtualenv_dir}
export ZTPS_INSTALL_ROOT=$RPM_BUILD_ROOT/%{app_virtualenv_dir}
export X_SCLS=python27
source /opt/rh/python27/enable
source $RPM_BUILD_DIR%{app_virtualenv_dir}/bin/activate

# Install prerequisites to enable offline installs
pip install -r requirements.txt

# Move necessary file from RPM_BUILD_DIR into RPM_BUILD_ROOT:
%{__install} -d $RPM_BUILD_ROOT%{app_virtualenv_dir}
cp -rp $RPM_BUILD_DIR%{app_virtualenv_dir}/* $RPM_BUILD_ROOT%{app_virtualenv_dir}
%else
export ZTPS_INSTALL_ROOT=$RPM_BUILD_ROOT
%endif

# Allow us to install libs in to RPM_BUILD_ROOT
# Force some paths for install to handle the virtual_env case for RHEL
%{__install} -d $RPM_BUILD_ROOT%{python2_sitelib}
PYTHONPATH=$RPM_BUILD_ROOT%{python2_sitelib}:${PYTHONPATH} \
python setup.py install --root=$RPM_BUILD_ROOT \
--install-scripts=%{_bindir} \
--install-lib=%{python2_sitelib}

%{__install} -pD conf/%{name}-wsgi.conf $RPM_BUILD_ROOT%{httpd_dir}/%{name}-wsgi.conf


%pre
getent group %{app_user} > /dev/null || groupadd -r %{app_user}
getent passwd %{app_user} > /dev/null || \
  useradd -m -g %{app_user} -d %{apphomedir} -s /bin/false \
  -c "%{name} - Server" %{app_user}
%if 0%{?rhel} == 6
datadir=/usr/share/ztpserver
%else
datadir=%{ztps_data_root}
%endif
if [ $1 -eq 0 ] ; then
    # This is an upgrade instead of a new install
    if [ -d %{_sysconfdir}/ztpserver ]; then
        cp -rp %{_sysconfdir}/ztpserver %{_sysconfdir}/ztpserver.rpmbak
    fi
    if [ -d ${datadir} ]; then
        # Copy the contents even if the top-level dir is a symlink
        mkdir -p ${datadir}.rpmbak
        cd ${datadir}.rpmbak
        cp -rp ${datadir}/. .
    fi
fi
exit 0

%posttrans


%post
%if 0%{?rhel} == 6
# Create symlinks for RHEL
if [ ! -d /usr/share/ztpserver ]; then
    ln -s %{ztps_data_root} /usr/share/ztpserver
fi
if [ ! -d /etc/ztpserver ]; then
    ln -s %{_sysconfdir}/ztpserver /etc/ztpserver
fi
ln -s -f %{_bindir}/ztps /usr/bin/ztps
%endif
# Ensure the server can read/write the necessary files.
# ZTPServer operators may be put in to this group to allow them to configure the service
chown -R %{app_user}:%{app_user} %{apphomedir}
chmod -R ug+rw %{ztps_data_root}
chcon -Rv --type=httpd_sys_content_t %{ztps_data_root} > /dev/null 2>&1

%preun
# $1 --> if 0, then it is a deinstall
# $1 --> if 1, then it is an upgrade


%postun
# $1 --> if 0, then it is a deinstall
# $1 --> if 1, then it is an upgrade
if [ $1 -eq 0 ] ; then
    # This is a removal, not an upgrade
    #  $1 versions will remain after this uninstall

    # Clean up symlinks
    [ -L /etc/ztpserver ] && rm -rf /etc/ztpserver
    [ -L /usr/share/ztpserver ] && rm -rf /usr/share/ztpserver
    [ -L /usr/bin/ztps ] && rm -rf /usr/bin/ztps
    [ -L %{httpd_dir}/%{name}-wsgi.conf ] && rm -rf %{httpd_dir}/%{name}-wsgi.conf
%if 0%{?rhel} == 6
    rm -rf %{app_virtualenv_dir}
%endif
fi

%files
# all the files to be included in this RPM:
%defattr(-,root,root,)
%if 0%{?rhel} == 6
%defattr(-,%{app_user},%{app_user},)
%{app_virtualenv_dir}/include
%{app_virtualenv_dir}/bin
%{app_virtualenv_dir}/lib*
%else
%{python2_sitelib}/%{name}
%{python2_sitelib}/%{name}-%{version}*.egg-info
%{_bindir}/ztps
%endif
%{_bindir}/ztps

%dir %{_sysconfdir}/ztpserver
%{_sysconfdir}/ztpserver/.VERSION
%config(noreplace) %{_sysconfdir}/ztpserver/ztpserver.conf
%config(noreplace) %{_sysconfdir}/ztpserver/ztpserver.wsgi
%config(noreplace) %{httpd_dir}/%{name}-wsgi.conf

%defattr(0775,%{app_user},%{app_user},)
%dir %{ztps_data_root}
%dir %{ztps_data_root}/actions
%dir %{ztps_data_root}/plugins
%dir %{ztps_data_root}/bootstrap
%dir %{ztps_data_root}/definitions
%dir %{ztps_data_root}/files
%dir %{ztps_data_root}/files/lib
%dir %{ztps_data_root}/nodes
%dir %{ztps_data_root}/resources

%defattr(0665,%{app_user},%{app_user},)
%{ztps_data_root}/files/lib/*
%config(noreplace) %{ztps_data_root}/actions/*
%config(noreplace) %{ztps_data_root}/plugins/*
%config(noreplace) %{ztps_data_root}/bootstrap/*
%config(noreplace) %{ztps_data_root}/neighbordb

%clean
rm -rf $RPM_BUILD_ROOT


%changelog
* Fri Mar 06 2015 Arista Networks <eosplus-dev@arista.com> - 1.3.2-1
- Update source0 to use package built by `python setup.py sdist`
- Quiet the output of `chcon` in post
- Move ztpserver-wsgi.conf to the primary source package
- Fix issue where rpm upgrade will remove some config files
* Wed Jan 28 2015 Arista Networks <eosplus-dev@arista.com> - 1.2.0-3
- Fixed installation path for virtual_env build
- Fixed permissions and home directory for virtual_env build
- Modified built-in macros for RHEL6 to simplify %files section
- Added env var ZTPS_INSTALL_[PREFIX|ROOT] to fix issues with setup.py
- Added symlinks from:
  - virtual_env/usr/share/ztpserver to /usr/share/ztpserver
  - virtual_env/%{_bindir}/ztps to /usr/bin/ztps
  - virtual_env/%{_confdir}ztpserver.[wsgi|conf] to /etc/ztpserver/
- Add post-un script to remove the symlinks created above

* Thu Dec 18 2014 Jere Julian <jere@arista.com> - 1.2.1
- For RHEL, only, update python sitelib and pip requirements
  for offline-capable packages

* Fri Nov 14 2014 Jere Julian <jere@arista.com>
- Increase utilization of built-in macros
- Replace define (runtime expansion) with global (immediate)
- Add app_url
- Disable the -debug package fro being built
- Source0 now has version-info and unpacks in to a versioned dir
- Remove manual override of BuildRoot
- Move python setup.py install to install
- Force some install path info for python setup so it properly places files, both in and out of a virtualenv
- Replace "cp -rp and mkdir -p" with __install
- Consolidate useradd code in pre and change the user/s HOME
- Remove symlinks on virtualenv systems (rhel6) as paths are fixed
- Remove userdel from preun as we can't guarantee other file ownership
- Specifically call out directories, config files, and permissions in files
- Fix rpmlint issues
  - Make setup quiet
  - dynamically define python2_sitelib and sitearch
  - Use a standard Group:

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
