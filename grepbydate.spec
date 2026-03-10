Name: grepbydate
Version: 0.0.0
Release: py3
Summary: Show events from log files converting input date formats to a unique format: '%Y-%m-%d %H:%M:%S'.

License: GPLv3
URL:            https://github.com/pafernanr/grepbydate
Source0: https://github.com/pafernanr/%{name}-%{version}.tar.gz
Group: Applications/System
BuildArch: noarch

BuildRoot: %{_tmppath}/%{name}-buildroot
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

%description
Show events from log files converting input date formats to a unique format: '%Y-%m-%d %H:%M:%S'.

%prep
%setup -qn %{name}-%{version}

%build

%install
rm -rf ${RPM_BUILD_ROOT}

mkdir -p ${RPM_BUILD_ROOT}/usr/lib/tools/grepbydate/bin
install -D -m 755 grepbydate/bin/__init__.py ${RPM_BUILD_ROOT}/usr/lib/tools/grepbydate/bin/__init__.py
cp -rp grepbydate ${RPM_BUILD_ROOT}/usr/lib/tools/

rm -rf ${RPM_BUILD_ROOT}/usr/lib/tools/%{name}/lib/__pycache__

%post
ln -s -f /usr/lib/tools/grepbydate/bin/__init__.py /usr/bin/grepbydate

%postun
if [ $1 -eq 0 ] ; then
    rm -f /usr/bin/%{name}
fi

%clean
rm -rf ${RPM_BUILD_ROOT}

%files
%defattr(-,root,root,-)
/usr/lib/tools/grepbydate
