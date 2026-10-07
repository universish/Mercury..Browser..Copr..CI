Name:           mercury-browser
Version:        1.0.0
Release:        1%{?dist}
Summary:        Compiler-optimized Chromium fork tuned for NVIDIA, AMD, and Intel hardware acceleration
License:        BSD-3-Clause AND MIT
URL:            https://github.com/Alex313031/Mercury
ExclusiveArch:  x86_64 aarch64

Source0:        mercury-payload-x86_64.tar.gz
Source1:        mercury-payload-aarch64.tar.gz
Source2:        mercury-launcher.sh
Source3:        mercury-browser.desktop
Source4:        mercury-browser.metainfo.xml

Requires:       libva
Requires:       libva-utils
Requires:       mesa-va-drivers
Recommends:     nvidia-vaapi-driver
Recommends:     libva-intel-driver
Recommends:     intel-media-driver

BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib

# İkili dosyalarda gereksiz strip ve build-id çakışmalarını engelleme
%global debug_package %{nil}
%global __strip /bin/true
%undefine _missing_build_ids_terminate_build

%description
Mercury is a compiler-optimized fork of Chromium built with AVX2 instruction sets
on x86_64 and NEON extensions on ARM64. This package includes an intelligent wrapper
for zero-configuration GPU hardware acceleration routing.

%prep
%ifarch x86_64
%setup -q -c -T -a 0 -n mercury-extracted
%endif

%ifarch aarch64
%setup -q -c -T -a 1 -n mercury-extracted
%endif

%build
# İkili paket doğrudan hazırlandığı için derleme adımı gerekmez

%install
rm -rf %{buildroot}

# Uygulama kök dizini
mkdir -p %{buildroot}/opt/mercury-browser
cp -a * %{buildroot}/opt/mercury-browser/

# Başlatıcı sarmalayıcı
install -Dm755 %{SOURCE2} %{buildroot}%{_bindir}/mercury-browser

# Masaüstü ve AppStream dosyaları
install -Dm644 %{SOURCE3} %{buildroot}%{_datadir}/applications/mercury-browser.desktop
install -Dm644 %{SOURCE4} %{buildroot}%{_datadir}/metainfo/mercury-browser.metainfo.xml

# Simgelerin yerleştirilmesi
for size in 16 24 32 48 64 128 256; do
    for logo in "%{buildroot}/opt/mercury-browser/product_logo_${size}.png" "%{buildroot}/opt/mercury-browser/mercury_${size}.png"; do
        if [ -f "$logo" ]; then
            install -Dm644 "$logo" "%{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/mercury-browser.png"
            break
        fi
    done
done

# Varsayılan şablon konfigürasyonu
mkdir -p %{buildroot}%{_sysconfdir}/mercury
cat << 'EOF' > %{buildroot}%{_sysconfdir}/mercury/mercury-flags.conf
--ozone-platform=x11
--enable-features=VaapiVideoDecodeLinuxGL,VaapiVideoEncoderLinuxGL
--ignore-gpu-blocklist
--enable-zero-copy
--use-gl=angle
--use-angle=gl
EOF

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/mercury-browser.desktop
appstream-util validate-relax --nonet %{buildroot}%{_datadir}/metainfo/mercury-browser.metainfo.xml

%files
/opt/mercury-browser
%{_bindir}/mercury-browser
%{_datadir}/applications/mercury-browser.desktop
%{_datadir}/metainfo/mercury-browser.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/mercury-browser.png
%config(noreplace) %{_sysconfdir}/mercury/mercury-flags.conf

%post
/usr/bin/update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%postun
/usr/bin/update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%changelog
* Wed Oct 07 2026 universish <universish@fedoraproject.org> - %{version}-%{release}
- Automated packaging for AVX2 and ARM64.
