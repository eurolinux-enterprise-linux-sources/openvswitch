%global _hardened_build 1


# This provides a way for distros that doesn't provide
# python-twisted-conch to disable building of ovsdbmonitor
# by default. You can override by passing --with ovsdbmonitor
# or --without ovsdbmonitor while building the RPM.
%define _pkg_ovsdbmonitor 0

%if %{?_with_ovsdbmonitor: 1}%{!?_with_ovsdbmonitor: 0}
%define with_ovsdbmonitor 1
%else
%define with_ovsdbmonitor %{?_without_ovsdbmonitor: 0}%{!?_without_ovsdbmonitor: %{_pkg_ovsdbmonitor}}
%endif

Name:           openvswitch
Version:        2.0.0
Release:        7%{?dist}
Summary:        Open vSwitch daemon/database/utilities

# Nearly all of openvswitch is ASL 2.0.  The bugtool is LGPLv2+, and the
# lib/sflow*.[ch] files are SISSL
# datapath/ is GPLv2 (although not built into any of the binary packages)
# python/compat is Python (although not built into any of the binary packages)
License:        ASL 2.0 and LGPLv2+ and SISSL
URL:            http://openvswitch.org
Source0:        http://openvswitch.org/releases/%{name}-%{version}.tar.gz
Source3:        openvswitch.logrotate
Source6:        ovsdbmonitor.desktop
Source9:        README.RHEL

Patch1: openvswitch-util-use-gcc-builtins-to-better-check-array-sizes.patch
Patch2: openvswitch-fedora-package-fix-systemd-ordering-and-deps.patch
Patch3: openvswitch-initscripts-add-tunnel-support.patch
Patch4: openvswitch-rhel-Enable-DHCP-support-for-internal-ports.patch

ExcludeArch:    ppc

BuildRequires:  systemd-units openssl openssl-devel
BuildRequires:  python python-twisted-core python-zope-interface PyQt4
BuildRequires:  desktop-file-utils
BuildRequires:  groff graphviz
%if %{with_ovsdbmonitor}
BuildRequires:  python-twisted-conch
%endif

Requires:       openssl iproute module-init-tools

Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units

%description
Open vSwitch provides standard network bridging functions and
support for the OpenFlow protocol for remote per-flow control of
traffic.

%package -n python-openvswitch
Summary:        Open vSwitch python bindings
License:        ASL 2.0
BuildArch:      noarch
Requires:       python

%description -n python-openvswitch
Python bindings for the Open vSwitch database

%if %{with_ovsdbmonitor}
%package -n ovsdbmonitor
Summary:        Open vSwitch graphical monitoring tool
License:        ASL 2.0
BuildArch:      noarch
Requires:       python-openvswitch = %{version}-%{release}
Requires:       python python-twisted-core python-twisted-conch python-zope-interface PyQt4

%description -n ovsdbmonitor
A GUI tool for monitoring and troubleshooting local or remote Open
vSwitch installations.  It presents GUI tables that graphically represent
an Open vSwitch kernel flow table (similar to "ovs-dpctl dump-flows")
and Open vSwitch database contents (similar to "ovs-vsctl list <table>").
%endif

%package test
Summary:        Open vSwitch testing utilities
License:        ASL 2.0
BuildArch:      noarch
Requires:       python-openvswitch = %{version}-%{release}
Requires:       python python-twisted-core python-twisted-web

%description test
Utilities that are useful to diagnose performance and connectivity
issues in Open vSwitch setup.

%package controller
Summary:        Open vSwitch OpenFlow controller
License:        ASL 2.0
Requires:       openvswitch = %{version}-%{release}

%description controller
Simple reference implementation of an OpenFlow controller for Open
vSwitch. Manages any number of remote switches over OpenFlow protocol,
causing them to function as L2 MAC-learning switches or hub.

%prep
%setup -q
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1

%build
%configure --enable-ssl --with-pkidir=%{_sharedstatedir}/openvswitch/pki
make %{?_smp_mflags}


%install
make install DESTDIR=$RPM_BUILD_ROOT

install -d -m 0755 $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch

install -p -D -m 0644 \
	rhel/usr_share_openvswitch_scripts_systemd_sysconfig.template \
	$RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/openvswitch
install -p -D -m 0644 \
	rhel/usr_lib_systemd_system_openvswitch.service \
	$RPM_BUILD_ROOT%{_unitdir}/openvswitch.service
install -p -D -m 0644 \
	rhel/usr_lib_systemd_system_openvswitch-nonetwork.service \
	$RPM_BUILD_ROOT%{_unitdir}/openvswitch-nonetwork.service

install -p -D -m 0755 rhel/etc_init.d_openvswitch \
	$RPM_BUILD_ROOT%{_datadir}/openvswitch/scripts/openvswitch.init

install -p -D -m 0644 %{SOURCE3} $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/openvswitch

install -d -m 0755 $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/network-scripts/
install -p -m 0755 rhel/etc_sysconfig_network-scripts_ifdown-ovs \
	$RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/network-scripts/ifdown-ovs
install -p -m 0755 rhel/etc_sysconfig_network-scripts_ifup-ovs \
	$RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/network-scripts/ifup-ovs

install -d -m 0755 $RPM_BUILD_ROOT/%{_sharedstatedir}/openvswitch

install -d -m 0755 $RPM_BUILD_ROOT%{python_sitelib}
mv $RPM_BUILD_ROOT/%{_datadir}/openvswitch/python/* $RPM_BUILD_ROOT%{python_sitelib}
rmdir $RPM_BUILD_ROOT/%{_datadir}/openvswitch/python/

mkdir -p $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
install -p -m 0644 %{SOURCE9} $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}

# Get rid of stuff we don't want to make RPM happy.
rm -f \
    $RPM_BUILD_ROOT%{_sbindir}/ovs-vlan-bug-workaround \
    $RPM_BUILD_ROOT%{_mandir}/man8/ovs-vlan-bug-workaround.8 \
    $RPM_BUILD_ROOT%{_sbindir}/ovs-brcompatd \
    $RPM_BUILD_ROOT%{_mandir}/man8/ovs-brcompatd.8

desktop-file-install --dir=$RPM_BUILD_ROOT%{_datadir}/applications %{SOURCE6}

%if ! %{with_ovsdbmonitor}
rm -f $RPM_BUILD_ROOT%{_bindir}/ovsdbmonitor
rm -f $RPM_BUILD_ROOT%{_mandir}/man1/ovsdbmonitor.1*
rm -rf $RPM_BUILD_ROOT%{_datadir}/ovsdbmonitor
rm -f $RPM_BUILD_ROOT%{_datadir}/applications/ovsdbmonitor.desktop
rm -rf $RPM_BUILD_ROOT%{_docdir}/ovsdbmonitor
%endif


%post
%if 0%{?systemd_post:1}
    %systemd_post %{name}.service
%else
    # Package install, not upgrade
    if [ $1 -eq 1 ]; then
        /bin/systemctl daemon-reload >dev/null || :
    fi
%endif

# Package with native systemd unit file is installed for the first time
%triggerun -- %{name} < 1.9.0-1
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply openvswitch
# to migrate them to systemd targets
/usr/bin/systemd-sysv-convert --save %{name} >/dev/null 2>&1 ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del %{name} >/dev/null 2>&1 || :
/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :

%preun
%if 0%{?systemd_preun:1}
    %systemd_preun %{name}.service
%else
    if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
        /bin/systemctl --no-reload disable %{name}.service >/dev/null 2>&1 || :
        /bin/systemctl stop %{name}.service >/dev/null 2>&1 || :
    fi
%endif

%postun
%if 0%{?systemd_postun_with_restart:1}
    %systemd_postun_with_restart %{name}.service
%else
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
    if [ "$1" -ge "1" ] ; then
    # Package upgrade, not uninstall
        /bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
    fi
%endif

%files
%{_sysconfdir}/openvswitch/
%config(noreplace) %{_sysconfdir}/logrotate.d/openvswitch
%config(noreplace) %{_sysconfdir}/sysconfig/openvswitch
%{_sysconfdir}/sysconfig/network-scripts/ifup-ovs
%{_sysconfdir}/sysconfig/network-scripts/ifdown-ovs
%{_unitdir}/openvswitch.service
%{_unitdir}/openvswitch-nonetwork.service
%{_bindir}/ovs-appctl
%{_bindir}/ovs-benchmark
%{_bindir}/ovs-dpctl
%{_bindir}/ovs-dpctl-top
%{_bindir}/ovs-ofctl
%{_bindir}/ovs-pcap
%{_bindir}/ovs-pki
%{_bindir}/ovs-tcpundump
%{_bindir}/ovs-vsctl
%{_bindir}/ovsdb-client
%{_bindir}/ovsdb-tool
%{_bindir}/ovs-parse-backtrace
# ovs-bugtool is LGPLv2+
%{_sbindir}/ovs-bugtool
%{_sbindir}/ovs-vswitchd
%{_sbindir}/ovsdb-server
%{_mandir}/man1/ovs-benchmark.1*
%{_mandir}/man1/ovs-pcap.1*
%{_mandir}/man1/ovs-tcpundump.1*
%{_mandir}/man1/ovsdb-client.1*
%{_mandir}/man1/ovsdb-server.1*
%{_mandir}/man1/ovsdb-tool.1*
%{_mandir}/man5/ovs-vswitchd.conf.db.5*
%{_mandir}/man8/ovs-appctl.8*
%{_mandir}/man8/ovs-bugtool.8*
%{_mandir}/man8/ovs-ctl.8*
%{_mandir}/man8/ovs-dpctl.8*
%{_mandir}/man8/ovs-dpctl-top.8*
%{_mandir}/man8/ovs-ofctl.8*
%{_mandir}/man8/ovs-pki.8*
%{_mandir}/man8/ovs-vsctl.8*
%{_mandir}/man8/ovs-vswitchd.8*
%{_mandir}/man8/ovs-parse-backtrace.8*
# /usr/share/openvswitch/bugtool-plugins and
# /usr/share/openvswitch/scripts/ovs-bugtool* are LGPLv2+
%{_datadir}/openvswitch/
%{_sharedstatedir}/openvswitch
%{_docdir}/%{name}-%{version}/README.RHEL
# see COPYING for full licensing details
%doc COPYING DESIGN INSTALL.SSL NOTICE README WHY-OVS

%files -n python-openvswitch
%{python_sitelib}/ovs
%doc COPYING

%if %{with_ovsdbmonitor}
%files -n ovsdbmonitor
%{_bindir}/ovsdbmonitor
%{_mandir}/man1/ovsdbmonitor.1*
%{_datadir}/ovsdbmonitor
%{_datadir}/applications/ovsdbmonitor.desktop
%doc ovsdb/ovsdbmonitor/COPYING
%endif

%files test
%{_bindir}/ovs-test
%{_bindir}/ovs-vlan-test
%{_bindir}/ovs-l3ping
%{_mandir}/man8/ovs-test.8*
%{_mandir}/man8/ovs-vlan-test.8*
%{_mandir}/man8/ovs-l3ping.8*
%{python_sitelib}/ovstest

%files controller
%{_bindir}/ovs-controller
%{_mandir}/man8/ovs-controller.8*


%changelog
* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 2.0.0-7
- Mass rebuild 2014-01-24

* Wed Jan 15 2014 Flavio Leitner <fbl@redhat.com> - 2.0.0-6
- Enable DHCP support for internal ports
  (upstream commit 490db96efaf89c63656b192d5ca287b0908a6c77)

* Wed Jan 15 2014 Flavio Leitner <fbl@redhat.com> - 2.0.0-5
- disabled ovsdbmonitor packaging
  (upstream has removed the component)

* Wed Jan 15 2014 Flavio Leitner <fbl@redhat.com> - 2.0.0-4
- fedora package: fix systemd ordering and deps.
  (upstream commit b49c106ef00438b1c59876dad90d00e8d6e7b627)

* Wed Jan 15 2014 Flavio Leitner <fbl@redhat.com> - 2.0.0-3
- util: use gcc builtins to better check array sizes
  (upstream commit 878f1972909b33f27b32ad2ded208eb465b98a9b)

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 2.0.0-2
- Mass rebuild 2013-12-27

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 2.0.0-1
- updated to 2.0.0 (#1023184)

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-8
- applied upstream commit 7b75828bf5654c494a53fa57be90713c625085e2
  rhel: Option to create tunnel through ifcfg scripts.

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-7
- applied upstream commit 32aa46891af5e173144d672e15fec7c305f9a4f3
  rhel: Set STP of a bridge during bridge creation.

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-6
- applied upstream commit 5b56f96aaad4a55a26576e0610fb49bde448dabe
  rhel: Prevent duplicate ifup calls.

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-5
- applied upstream commit 79416011612541d103a1d396d888bb8c84eb1da4
  rhel: Return an exit value of 0 for ifup-ovs.

* Mon Oct 28 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-4
- applied upstream commit 2517bad92eec7e5625bc8b248db22fdeaa5fcde9
  Added RHEL ovs-ifup STP option handling

* Tue Oct 1 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-3
- don't use /var/lock/subsys with systemd (#1006412)

* Thu Sep 19 2013 Flavio Leitner <fbl@redhat.com> - 1.11.0-2
- ovsdbmonitor package is optional

* Thu Aug 29 2013 Thomas Graf <tgraf@redhat.com> - 1.11.0-1
- Update to 1.11.0

* Tue Aug 13 2013 Flavio Leitner <fbl@redhat.com> - 1.10.0-7
- Fixed openvswitch-nonetwork to start openvswitch.service (#996804)

* Sat Aug 03 2013 Petr Pisar <ppisar@redhat.com> - 1.10.0-6
- Perl 5.18 rebuild

* Tue Jul 23 2013 Thomas Graf <tgraf@redhat.com> - 1.10.0-5
- Typo

* Tue Jul 23 2013 Thomas Graf <tgraf@redhat.com> - 1.10.0-4
- Spec file fixes
- Maintain local copy of sysconfig.template

* Thu Jul 18 2013 Petr Pisar <ppisar@redhat.com> - 1.10.0-3
- Perl 5.18 rebuild

* Mon Jul 01 2013 Thomas Graf <tgraf@redhat.com> - 1.10.0-2
- Enable PIE (#955181)
- Provide native systemd unit files (#818754)

* Thu May 02 2013 Thomas Graf <tgraf@redhat.com> - 1.10.0-1
- Update to 1.10.0 (#958814)

* Thu Feb 28 2013 Thomas Graf <tgraf@redhat.com> - 1.9.0-1
- Update to 1.9.0 (#916537)

* Tue Feb 12 2013 Thomas Graf <tgraf@redhat.com> - 1.7.3-8
- Fix systemd service dependency loop (#818754)

* Fri Jan 25 2013 Thomas Graf <tgraf@redhat.com> - 1.7.3-7
- Auto-start openvswitch service on ifup/ifdown (#818754)
- Add OVSREQUIRES to allow defining OpenFlow interface dependencies

* Thu Jan 24 2013 Thomas Graf <tgraf@redhat.com> - 1.7.3-6
- Update to Open vSwitch 1.7.3

* Tue Nov 20 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1-6
- Increase max fd limit to support 256 bridges (#873072)

* Thu Nov  1 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1-5
- Don't create world writable pki/*/incomming directory (#845351)

* Thu Oct 25 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1-4
- Don't add iptables accept rule for -p GRE as GRE tunneling is unsupported

* Tue Oct 16 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1-3
- require systemd instead of systemd-units to use macro helpers (#850258)

* Tue Oct  9 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1-2
- make ovs-vsctl timeout if daemon is not running (#858722)

* Mon Sep 10 2012 Thomas Graf <tgraf@redhat.com> - 1.7.1.-1
- Update to 1.7.1

* Fri Sep  7 2012 Thomas Graf <tgraf@redhat.com> - 1.7.0.-3
- add controller package containing ovs-controller

* Thu Aug 23 2012 Tomas Hozza <thozza@redhat.com> - 1.7.0-2
- fixed SPEC file so it comply with new systemd-rpm macros guidelines (#850258)

* Fri Aug 17 2012 Tomas Hozza <thozza@redhat.com> - 1.7.0-1
- Update to 1.7.0
- Fixed openvswitch-configure-ovskmod-var-autoconfd.patch because
  openvswitch kernel module name changed in 1.7.0
- Removed Source8: ovsdbmonitor-move-to-its-own-data-directory.patch
- Patches merged:
  - ovsdbmonitor-move-to-its-own-data-directory-automaked.patch
  - openvswitch-rhel-initscripts-resync.patch

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Mar 15 2012 Chris Wright <chrisw@redhat.com> - 1.4.0-5
- fix ovs network initscripts DHCP address acquisition (#803843)

* Tue Mar  6 2012 Chris Wright <chrisw@redhat.com> - 1.4.0-4
- make BuildRequires openssl explicit (needed on f18/rawhide now)

* Tue Mar  6 2012 Chris Wright <chrisw@redhat.com> - 1.4.0-3
- use glob to catch compressed manpages

* Thu Mar  1 2012 Chris Wright <chrisw@redhat.com> - 1.4.0-2
- Update License comment, use consitent macros as per review comments bz799171

* Wed Feb 29 2012 Chris Wright <chrisw@redhat.com> - 1.4.0-1
- Initial package for Fedora
