%define undotted_version %(echo %{version} |sed -e 's,\\\.,,g')
Name: 7zip
Version: 24.09
Release: 3
Source0: https://www.7-zip.org/a/7z%{undotted_version}-src.tar.xz
Source1: p7zip
Source2: p7zip.1
# Known to crash 7zip 24.09 on znver1 if
# built with cmpl_clang_x64.mak and MY_ASM=uasm
Source5: 7zip_crasher.7z
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
sed -i 's/LFLAGS_STRIP = -s/LFLAGS_STRIP =/' CPP/7zip/7zip_gcc.mak
sed -i 's/$(CXX) -o $(PROGPATH)/$(CXX) -Wl,-z,noexecstack -o $(PROGPATH)/' CPP/7zip/7zip_gcc.mak

%build
cd CPP/7zip/Bundles/Alone2
# FIXME we may want to enable hand-crafted asm code by using
# cmpl_clang_x64.mak
# cmpl_clang_x86.mak
# cmpl_clang_arm64.mak
# Just make sure it doesn't break the test case checked for in %%check
if echo %{__cc} |grep -q clang; then
	%make_build -f ../../cmpl_clang.mak
else
	%make_build -f ../../cmpl_gcc.mak
fi

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

%if ! %{?cross_compiling}
%check
echo Password |%{_bindir}/7z l %{S:5}
%endif

%files
%license DOC/copying.txt DOC/License.txt
%doc DOC/readme.txt DOC/7zC.txt DOC/Methods.txt DOC/src-history.txt
%{_bindir}/7z
%{_bindir}/7za
%{_bindir}/7zr
%{_bindir}/7zz
%{_bindir}/p7zip
%{_mandir}/man1/p7zip.1*
