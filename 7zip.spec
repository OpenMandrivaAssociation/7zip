%define _empty_manifest_terminate_build 0

%define undotted_version %(echo %{version} |sed -e 's,\\\.,,g')
Name: 7zip
Version: 24.05
Release: 1
Source0: https://www.7-zip.org/a/7z%{undotted_version}-src.tar.xz
Source1: p7zip
Source2: p7zip.1
Summary: File Archiver
URL: https://www.7-zip.org/
License: BSD-3-Clause AND LGPL-2.1-or-later
Group: Archiving/Compression
%ifarch %{x86_64}
BuildRequires: uasm
%endif
BuildRequires: dos2unix
BuildRequires: make
Obsoletes: p7zip < %{EVRD}

%description
This package contains the 7z command line utility for archiving and
extracting various formats.

%prep
%autosetup -p1 -c -n %{name}-%{version}
dos2unix DOC/*.txt
chmod -x DOC/*.txt
# Inject CFLAGS
sed -i 's/^ -fPIC/ -fPIC %{optflags} -fno-strict-aliasing/' CPP/7zip/7zip_gcc.mak
sed -i 's/LFLAGS_ALL = -s/LFLAGS_ALL =/' CPP/7zip/7zip_gcc.mak
sed -i 's/$(CXX) -o $(PROGPATH)/$(CXX) -Wl,-z,noexecstack -o $(PROGPATH)/' CPP/7zip/7zip_gcc.mak

%if 0
if echo %{__cc} |grep -q clang; then
	# Get rid of gcc specific options
	find . -name warn_gcc.mak |xargs sed -i -e 's,-Waggressive-loop-optimizations,,;s,-Wbool-compare,,;s,-Wcast-align=strict,-Wcast-align,g;s,-Wduplicated-branches,,g;s,-Wduplicated-cond,,;s,-Wformat-contains-nul,,;s,-Wimplicit-fallthrough=5,-Wimplicit-fallthrough,g'
fi
%endif

%build
# FIXME clang commented out for now, not working with clang 15
cd CPP/7zip/Bundles/Alone2
%ifarch %{x86_64}
%make_build -f ../../cmpl_gcc_x64.mak MY_ASM=uasm # CC=%{__cc} CXX=%{__cxx}
%else
%ifarch %{ix86}
%make_build -f ../../cmpl_gcc_x86.mak MY_ASM=uasm # CC=%{__cc} CXX=%{__cxx}
%else
%make_build -f ../../cmpl_gcc.mak # CC=%{__cc} CXX=%{__cxx}
%endif
%endif

%install
install -Dm 755 CPP/7zip/Bundles/Alone2/b/*/7zz %{buildroot}%{_bindir}/7zz
# Create links the executables provided by p7zip
ln -s 7zz %{buildroot}%{_bindir}/7z
ln -s 7z %{buildroot}%{_bindir}/7za
ln -s 7z %{buildroot}%{_bindir}/7zr
# Install p7zip wrapper and its manpage
install -m755 %{SOURCE1} %{buildroot}%{_bindir}/p7zip
install -m644 -Dt %{buildroot}%{_mandir}/man1 %{SOURCE2}
# Remove a mention of the p7zip-rar package that we don't have
sed -i 's/RAR (if the non-free p7zip-rar package is installed)//g' %{buildroot}%{_mandir}/man1/p7zip.1

%files
%license DOC/copying.txt DOC/License.txt
%doc DOC/readme.txt DOC/7zC.txt DOC/Methods.txt DOC/src-history.txt
%{_bindir}/7z
%{_bindir}/7za
%{_bindir}/7zr
%{_bindir}/7zz
%{_bindir}/p7zip
%{_mandir}/man1/p7zip.1*
