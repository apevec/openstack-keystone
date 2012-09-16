#
# This is 2012.1.2 stable/essex release
#
%global release_name essex
%global snapdate 20120810
%global git_revno 2230
%global snaptag %{?milestone:~%{release_letter}%{milestone}}~%{snapdate}.%{git_revno}
%global with_doc %{!?_without_doc:1}%{?_without_doc:0}

Name:           openstack-keystone
Version:        2012.1.2
Release:        4%{?dist}
Summary:        OpenStack Identity Service

License:        ASL 2.0
URL:            http://keystone.openstack.org/
Source0:        http://launchpad.net/keystone/%{release_name}/%{version}/+download/keystone-%{version}.tar.gz
#Source0:        http://tarballs.openstack.org/keystone/keystone-%{version}%{snaptag}.tar.gz
Source1:        openstack-keystone.logrotate
Source2:        openstack-keystone.service
Source5:        openstack-keystone-sample-data

#
# patches_base=2012.1.2
#
Patch0001: 0001-fix-man-page-build.patch
Patch0002: 0002-fix-sphinx-warnings.patch
Patch0003: 0003-match-egg-and-spec-requires.patch
Patch0004: 0004-Require-authz-to-update-user-s-tenant-bug-1040626.patch
Patch0005: 0005-List-tokens-for-memcached-backend.patch
Patch0006: 0006-Delete-user-tokens-after-role-grant-revoke.patch
Patch0007: 0007-Limit-token-revocation-to-tenant-bug-1050025.patch

BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python-sphinx >= 1.0
BuildRequires:  openstack-utils
BuildRequires:  python-iniparse
BuildRequires:  systemd-units

Requires:       python-keystone = %{version}-%{release}
Requires:       python-keystoneclient >= 2012.1-0.4.e4

Requires(post):   systemd-units
Requires(preun):  systemd-units
Requires(postun): systemd-units
Requires(pre):    shadow-utils

%description
Keystone is a Python implementation of the OpenStack
(http://www.openstack.org) identity service API.

This package contains the Keystone daemon.

%package -n       python-keystone
Summary:          Keystone Python libraries
Group:            Applications/System
# python-keystone added in 2012.1-0.2.e3
Conflicts:      openstack-keystone < 2012.1-0.2.e3

# to pull middleware on yum update
Requires:       python-keystone-auth-token = %{version}-%{release}

Requires:       python-eventlet
Requires:       python-ldap
Requires:       python-lxml
Requires:       python-memcached
Requires:       python-migrate
Requires:       python-paste-deploy
Requires:       python-routes
Requires:       python-sqlalchemy
Requires:       python-webob
Requires:       python-passlib
Requires:       MySQL-python
Requires:       PyPAM

%description -n   python-keystone
Keystone is a Python implementation of the OpenStack
(http://www.openstack.org) identity service API.

This package contains the Keystone Python library.

%package -n     python-keystone-auth-token
Summary:        Keystone Authentication Middleware.
Group:          Applications/System
# python-keystone-auth-token added in 2012.1-3
Conflicts:      python-keystone < 2012.1-3

Requires:       python-iso8601
Requires:       python-memcached
Requires:       python-webob

%description -n   python-keystone-auth-token
Keystone is a Python implementation of the OpenStack
(http://www.openstack.org) identity service API.

This package contains the Keystone Authentication Middleware.

%if 0%{?with_doc}
%package doc
Summary:        Documentation for OpenStack Identity Service
Group:          Documentation

Requires:       %{name} = %{version}-%{release}

%description doc
Keystone is a Python implementation of the OpenStack
(http://www.openstack.org) identity service API.

This package contains documentation for Keystone.
%endif

%prep
%setup -q -n keystone-%{version}

%patch0001 -p1
%patch0002 -p1
%patch0003 -p1
%patch0004 -p1
%patch0005 -p1
%patch0006 -p1
%patch0007 -p1

find . \( -name .gitignore -o -name .placeholder \) -delete
find keystone -name \*.py -exec sed -i '/\/usr\/bin\/env python/d' {} \;


%build
# change default configuration
openstack-config --set etc/keystone.conf DEFAULT log_file %{_localstatedir}/log/keystone/keystone.log
openstack-config --set etc/keystone.conf sql connection mysql://keystone:keystone@localhost/keystone
openstack-config --set etc/keystone.conf catalog template_file %{_sysconfdir}/keystone/default_catalog.templates
openstack-config --set etc/keystone.conf catalog driver keystone.catalog.backends.sql.Catalog
openstack-config --set etc/keystone.conf identity driver keystone.identity.backends.sql.Identity
openstack-config --set etc/keystone.conf token driver keystone.token.backends.sql.Token
openstack-config --set etc/keystone.conf ec2 driver keystone.contrib.ec2.backends.sql.Ec2

%{__python} setup.py build

%install
%{__python} setup.py install --skip-build --root %{buildroot}

# Delete tests
rm -fr %{buildroot}%{python_sitelib}/tests
rm -fr %{buildroot}%{python_sitelib}/run_tests.*

install -d -m 755 %{buildroot}%{_sysconfdir}/keystone
install -p -D -m 640 etc/keystone.conf %{buildroot}%{_sysconfdir}/keystone/keystone.conf
install -p -D -m 640 etc/default_catalog.templates %{buildroot}%{_sysconfdir}/keystone/default_catalog.templates
install -p -D -m 640 etc/policy.json %{buildroot}%{_sysconfdir}/keystone/policy.json
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/logrotate.d/openstack-keystone
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/openstack-keystone.service
# Install sample data script.
install -p -D -m 755 tools/sample_data.sh %{buildroot}%{_datadir}/%{name}/sample_data.sh
install -p -D -m 755 %{SOURCE5} %{buildroot}%{_bindir}/openstack-keystone-sample-data

install -d -m 755 %{buildroot}%{_sharedstatedir}/keystone
install -d -m 755 %{buildroot}%{_localstatedir}/log/keystone

# docs generation requires everything to be installed first
export PYTHONPATH="$( pwd ):$PYTHONPATH"
pushd doc
if [ -x /usr/bin/sphinx-apidoc ]; then
    make html
    make man
else
    make html SPHINXAPIDOC=echo
    make man SPHINXAPIDOC=echo
fi
mkdir -p %{buildroot}%{_mandir}/man1
install -p -D -m 644 build/man/*.1 %{buildroot}%{_mandir}/man1/
popd
# Fix hidden-file-or-dir warnings
rm -fr doc/build/html/.doctrees doc/build/html/.buildinfo

%pre
# 163:163 for keystone (openstack-keystone) - rhbz#752842
getent group keystone >/dev/null || groupadd -r --gid 163 keystone
getent passwd keystone >/dev/null || \
useradd --uid 163 -r -g keystone -d %{_sharedstatedir}/keystone -s /sbin/nologin \
-c "OpenStack Keystone Daemons" keystone
exit 0

%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%post -n python-keystone-auth-token
# workaround for rhbz 824034#c14
if [ ! -e %{python_sitelib}/keystone/__init__.py ]; then
    > %{python_sitelib}/keystone/__init__.py
fi
if [ ! -e %{python_sitelib}/keystone/middleware/__init__.py ]; then
    > %{python_sitelib}/keystone/middleware/__init__.py
fi

%triggerpostun -n python-keystone-auth-token -- python-keystone
# edge case: removing python-keystone with overlapping files
if [ $2 -eq 0 ] ; then
    # Package removal, not upgrade
    > %{python_sitelib}/keystone/__init__.py
    > %{python_sitelib}/keystone/middleware/__init__.py
fi

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable openstack-keystone.service > /dev/null 2>&1 || :
    /bin/systemctl stop openstack-keystone.service > /dev/null 2>&1 || :
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart openstack-keystone.service >/dev/null 2>&1 || :
fi

%files
%doc LICENSE
%doc README.rst
%{_mandir}/man1/keystone*.1.gz
%{_bindir}/keystone-all
%{_bindir}/keystone-manage
%{_bindir}/openstack-keystone-sample-data
%{_datadir}/%{name}
%{_unitdir}/openstack-keystone.service
%dir %{_sysconfdir}/keystone
%config(noreplace) %attr(-, root, keystone) %{_sysconfdir}/keystone/keystone.conf
%config(noreplace) %attr(-, root, keystone) %{_sysconfdir}/keystone/default_catalog.templates
%config(noreplace) %attr(-, keystone, keystone) %{_sysconfdir}/keystone/policy.json
%config(noreplace) %{_sysconfdir}/logrotate.d/openstack-keystone
%dir %attr(-, keystone, keystone) %{_sharedstatedir}/keystone
%dir %attr(-, keystone, keystone) %{_localstatedir}/log/keystone

%files -n python-keystone
%defattr(-,root,root,-)
%doc LICENSE
%{python_sitelib}/keystone
%exclude %{python_sitelib}/keystone/middleware/auth_token.py*
%{python_sitelib}/keystone-%{version}-*.egg-info

%files -n python-keystone-auth-token
%defattr(-,root,root,-)
%doc LICENSE
%dir %{python_sitelib}/keystone
%ghost %{python_sitelib}/keystone/__init__.py
%dir %{python_sitelib}/keystone/middleware
%ghost %{python_sitelib}/keystone/middleware/__init__.py
%{python_sitelib}/keystone/middleware/auth_token.py*

%if 0%{?with_doc}
%files doc
%doc LICENSE doc/build/html
%endif

%changelog
* Sun Sep 16 2012 Alan Pevec <apevec@redhat.com> 2012.1.2-4
- Limit token revocation to tenant (lp#1050025)

* Wed Sep 12 2012 Alan Pevec <apevec@redhat.com> 2012.1.2-3
- Delete user tokens after role grant/revoke (CVE-2012-4413)

* Thu Aug 30 2012 Alan Pevec <apevec@redhat.com> 2012.1.2-2
- Require authz to update user's tenant (CVE-2012-3542)

* Mon Aug 13 2012 Alan Pevec <apevec@redhat.com> 2012.1.2-1
- updated to stable essex release 2012.1.2

* Fri Jun 22 2012 Alan Pevec <apevec@redhat.com> 2012.1.1-1
- updated to stable essex release 2012.1.1 (CVE-2012-3426)

* Fri Jun 15 2012 Alan Pevec <apevec@redhat.com> 2012.1-5
- fix upgrade case with python-keystone-auth-token (rhbz#824034#c20)

* Mon Jun 11 2012 Alan Pevec <apevec@redhat.com> 2012.1-4
- Corrects url conversion in export_legacy_catalog (lp#994936)
- Invalidate user tokens when password is changed (lp#996595)
- Invalidate user tokens when a user is disabled (lp#997194)
- Carrying over token expiry time when token chaining (lp#998185)

* Thu May 24 2012 Alan Pevec <apevec@redhat.com> 2012.1-3
- python-keystone-auth-token subpackage (rhbz#824034)
- use reserved user id for keystone (rhbz#752842)

* Mon May 21 2012 Alan Pevec <apevec@redhat.com> 2012.1-2
- Sync up with Essex stable branch
- Remove dependencies no loner needed by Essex

* Thu Apr 05 2012 Alan Pevec <apevec@redhat.com> 2012.1-1
- Essex release

* Wed Apr 04 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.13.rc2
- essex rc2

* Sat Mar 24 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.12.rc1
- update to final essex rc1

* Wed Mar 21 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.11.rc1
- essex rc1

* Thu Mar 08 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.10.e4
- change default catalog backend to sql rhbz#800704
- update sample-data script
- add missing keystoneclient dependency

* Thu Mar 01 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.9.e4
- essex-4 milestone

* Sat Feb 25 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.8.e4
- change default database to mysql

* Tue Feb 21 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.7.e4
- switch all backends to sql

* Mon Feb 20 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.6.e4
- add missing default_catalog.templates

* Mon Feb 20 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.5.e4
- pre essex-4 snapshot, for keystone rebase

* Mon Feb 13 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.4.e3
- fix deps rhbz#787072
- keystone is not hashing passwords lp#924391
- Fix "KeyError: 'service-header-mappings'" lp#925872

* Wed Feb  8 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 2012.1-0.3.e3
- Remove the dep on python-sqlite2 as that's being retired in F17 and keystone
  will work with the sqlite3 module from the stdlib

* Thu Jan 26 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.2.e3
- separate library to python-keystone
- avoid conflict with python-keystoneclient

* Thu Jan 26 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.1.e3
- essex-3 milestone

* Wed Jan 18 2012 Alan Pevec <apevec@redhat.com> 2012.1-0.e2
- essex-2 milestone

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2011.3.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Thu Nov 24 2011 Alan Pevec <apevec@redhat.com> 2011.3.1-2
- include LICENSE, update package description from README.md

* Mon Nov 21 2011 Alan Pevec <apevec@redhat.com> 2011.3.1-1
- Update to 2011.3.1 stable/diablo release

* Fri Nov 11 2011 Alan Pevec <apevec@redhat.com> 2011.3-2
- Update to the latest stable/diablo snapshot

* Mon Oct 24 2011 Mark McLoughlin <markmc@redhat.com> - 2011.3-1
- Update version to diablo final

* Wed Oct 19 2011 Matt Domsch <Matt_Domsch@dell.com> - 1.0-0.4.d4.1213
- add Requires: python-passlib

* Mon Oct 3 2011 Matt Domsch <Matt_Domsch@dell.com> - 1.0-0.2.d4.1213
- update to diablo release.
- BR systemd-units for _unitdir

* Fri Sep  2 2011 Mark McLoughlin <markmc@redhat.com> - 1.0-0.2.d4.1078
- Use upstream snapshot tarball
- No need to define python_sitelib anymore
- BR python2-devel
- Remove BRs only needed for unit tests
- No need to clean buildroot in install anymore
- Use slightly more canonical site for URL tag
- Prettify the requires tags
- Cherry-pick tools.tracer patch from upstream
- Add config file
- Add keystone user and group
- Ensure log file is in /var/log/keystone
- Ensure the sqlite db is in /var/lib/keystone
- Add logrotate support
- Add system units

* Thu Sep  1 2011 Matt Domsch <Matt_Domsch@dell.com> - 1.0-0.1.20110901git396f0bfd%{?dist}
- initial packaging
