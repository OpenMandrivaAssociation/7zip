%define undotted_version %(echo %{version} |sed -e 's,\\\.,,g')
Name: 7zip
Version: 26.03
Release: 1
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
BuildRequires: asmc
%endif
BuildRequires: dos2unix
BuildRequires: make
# llvm-profdata for the %pgo merge step
BuildRequires: llvm
Obsoletes: p7zip < %{EVRD}

%patchlist

%description
This package contains the 7z command line utility for archiving and
extracting various formats.

%prep
%autosetup -p1 -c -n %{name}-%{version}
dos2unix DOC/*.txt
chmod -x DOC/*.txt
# Expand flags at compile/link time so %pgo generate/use flags apply.
# The makefile overwrites CFLAGS/LDFLAGS; rpm's script header also resets
# RPM_OPT_FLAGS, so pick up PGO flags from CFLAGS/LDFLAGS in %build.
sed -i 's/^ -fPIC/ -fPIC $(RPM_PGO_CFLAGS) -fno-strict-aliasing/' CPP/7zip/7zip_gcc.mak
sed -i 's/LFLAGS_ALL = -s/LFLAGS_ALL =/' CPP/7zip/7zip_gcc.mak
sed -i 's/LFLAGS_STRIP = -s/LFLAGS_STRIP =/' CPP/7zip/7zip_gcc.mak
sed -i 's/^LFLAGS_ALL = /LFLAGS_ALL = $(RPM_LD_FLAGS) /' CPP/7zip/7zip_gcc.mak
sed -i 's/$(CXX) -o $(PROGPATH)/$(CXX) -Wl,-z,noexecstack -o $(PROGPATH)/' CPP/7zip/7zip_gcc.mak
# Clang 23+ -Weverything -Werror: annotation suggestion, not a real defect
echo 'CFLAGS_WARN += -Wno-unknown-warning-option -Wno-lifetime-safety -Wno-lifetime-safety-intra-tu-suggestions -Wno-lifetime-safety-cross-tu-suggestions' >> CPP/7zip/warn_clang.mak

%build
%ifarch %{x86_64}
. %{_sysconfdir}/profile.d/asmc-profile.sh
%endif
# PGO setenv CFLAGS/LDFLAGS; rpm script header resets RPM_OPT_FLAGS
export RPM_PGO_CFLAGS="${CFLAGS:-${RPM_OPT_FLAGS}}"
export RPM_LD_FLAGS="${LDFLAGS:-${RPM_LD_FLAGS}}"

cd CPP/7zip/Bundles/Alone2
%ifarch %{x86_64}
PLAT=_x64
%else
%ifarch %{aarch64}
PLAT=_arm64
%else
%ifarch %{arm}
PLAT=_arm
%else
%ifarch %{ix86}
PLAT=_x86
%endif
%endif
%endif
%endif
if %{__cc} --version |grep -q clang; then
	%make_build -f ../../cmpl_clang$PLAT.mak $EXTRAARGS
else
	%make_build -f ../../cmpl_gcc$PLAT.mak $EXTRAARGS
fi

# Compress/extract/list/hash across common formats; also list the known crasher
%pgo
bin=
for f in CPP/7zip/Bundles/Alone2/b/*/7zz; do
	[ -x "$f" ] && bin=$f && break
done
if [ -z "$bin" ]; then
	echo "PGO: instrumented 7zz not found" >&2
	exit 1
fi
tdir=$(mktemp -d)
trap 'rm -rf "$tdir"' EXIT
mkdir -p "$tdir/in"
cp -a DOC C CPP/7zip/Common CPP/7zip/Compress CPP/7zip/Archive/7z "$tdir/in/"
dd if=/dev/urandom of="$tdir/in/rand.bin" bs=64k count=16 status=none
"$bin" a -bd -mx1 -mmt=on "$tdir/fast.7z" "$tdir/in"
"$bin" a -bd -mx5 -mmt=on "$tdir/norm.7z" "$tdir/in"
"$bin" a -bd -tzip -mx5 -mmt=on "$tdir/a.zip" "$tdir/in"
"$bin" a -bd -tgzip -mx5 "$tdir/a.gz" "$tdir/in/DOC/readme.txt"
"$bin" a -bd -txz -mx5 "$tdir/a.xz" "$tdir/in/DOC/readme.txt"
"$bin" a -bd -ttar "$tdir/a.tar" "$tdir/in"
"$bin" t -bd "$tdir/fast.7z"
"$bin" t -bd "$tdir/norm.7z"
"$bin" t -bd "$tdir/a.zip"
"$bin" l -bd "$tdir/norm.7z"
"$bin" x -bd -o"$tdir/o1" "$tdir/fast.7z"
"$bin" x -bd -o"$tdir/o2" "$tdir/a.zip"
"$bin" x -bd -o"$tdir/o3" "$tdir/a.tar"
"$bin" h -bd "$tdir/in"
echo Password | "$bin" l -bd -bb0 %{S:5} >/dev/null || :

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
echo Password |%{buildroot}%{_bindir}/7z l %{S:5}
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
