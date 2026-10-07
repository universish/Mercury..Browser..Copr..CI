Name:           mercury-browser
Version:        1.0.0
Release:        1%{?dist}
Summary:        Compiler-optimized browser fork tuned for NVIDIA, AMD, and Intel hardware acceleration
License:        MPL-2.0 AND BSD-3-Clause AND MIT
URL:            https://github.com/Alex313031/Mercury
ExclusiveArch:  x86_64 aarch64

Source0:        mercury-payload-x86_64.tar.gz
Source1:        mercury-payload-aarch64.tar.gz
Source2:        mercury-launcher.sh
Source3:        mercury-browser.desktop
Source4:        mercury-browser.metainfo.xml

Requires:       libva
Requires:       libva-utils

# Mimariye göre donanım hızlandırma paketleri
%ifarch x86_64
Recommends:     mesa-va-drivers
Recommends:     nvidia-vaapi-driver
Recommends:     libva-intel-driver
Recommends:     intel-media-driver
%endif

%ifarch aarch64
Recommends:     mesa-va-drivers
%endif

BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib

# İkili dosyalarda strip hatası ve build-id çakışmalarını engelleme
%global debug_package %{nil}
%global __strip /bin/true
%global _build_id_links none
%undefine _missing_build_ids_terminate_build

%description
Mercury is a compiler-optimized browser fork built with AVX2 instruction sets
on x86_64 and NEON extensions on ARM64. This package includes an intelligent
wrapper and pre-configured preferences for zero-configuration multi-GPU
hardware video acceleration routing on Linux.

%prep
%ifarch x86_64
%setup -q -c -T -a 0 -n mercury-extracted
%endif

%ifarch aarch64
%setup -q -c -T -a 1 -n mercury-extracted
%endif

%build
# İkili (pre-compiled) paketler açıldığı için derleme adımı gerekmez

%install
rm -rf %{buildroot}

mkdir -p %{buildroot}/opt/mercury-browser
cp -a * %{buildroot}/opt/mercury-browser/

# Başlatıcı sarmalayıcı (launcher)
install -Dm755 %{SOURCE2} %{buildroot}%{_bindir}/mercury-browser

# Masaüstü ve AppStream metaveri dosyaları
install -Dm644 %{SOURCE3} %{buildroot}%{_datadir}/applications/mercury-browser.desktop
install -Dm644 %{SOURCE4} %{buildroot}%{_datadir}/metainfo/mercury-browser.metainfo.xml

# Simgelerin yerleştirilmesi (Firefox dahili simgeleri ve olası fallback'ler taranır)
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/128x128/apps
ICON_FOUND=0
for size in 16 32 48 64 128; do
    for logo in "%{buildroot}/opt/mercury-browser/browser/chrome/icons/default/default${size}.png" \
                "%{buildroot}/opt/mercury-browser/product_logo_${size}.png" \
                "%{buildroot}/opt/mercury-browser/mercury_${size}.png" \
                "%{buildroot}/opt/mercury-browser/default${size}.png"; do
        if [ -f "$logo" ]; then
            install -Dm644 "$logo" "%{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/mercury-browser.png"
            ICON_FOUND=1
            break
        fi
    done
done

# Eğer döngüden simge çıkmazsa mevcut herhangi bir png dosyasını 128x128 simge olarak bağla
if [ $ICON_FOUND -eq 0 ]; then
    FALLBACK_PNG=$(find %{buildroot}/opt/mercury-browser/ -name "*.png" | head -n 1 || true)
    if [ -n "$FALLBACK_PNG" ]; then
        install -Dm644 "$FALLBACK_PNG" "%{buildroot}%{_datadir}/icons/hicolor/128x128/apps/mercury-browser.png"
    fi
fi

# NVIDIA donanım hızlandırma blok listesini aşan sistem geneli tercihler
mkdir -p %{buildroot}/opt/mercury-browser/defaults/pref
cat << 'EOF' > %{buildroot}/opt/mercury-browser/defaults/pref/gpu-acceleration.js
pref("media.ffmpeg.vaapi.enabled", true);
pref("media.rdd-ffmpeg.enabled", true);
pref("media.hardware-video-decoding.force-enabled", true);
pref("widget.dmabuf.force-enabled", true);
pref("gfx.x11-egl.force-enabled", true);
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
- Automated packaging with multi-format fallback (RPM -> DEB -> AppImage).
- Add StartupWMClass=mercury-default and force-enable NVIDIA hardware video decoding.
