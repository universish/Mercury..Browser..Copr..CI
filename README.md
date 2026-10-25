# Mercury Browser (AVX2 & ARM64) for Fedora Copr

[![Fedora Copr](https://img.shields.io/badge/Copr-universish%2FMercury-blue.svg)](https://copr.fedorainfracloud.org/coprs/universish/Mercury/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Arch-x86__64%20(AVX2)%20%7C%20aarch64-brightgreen.svg)]()
[![Target OS](https://img.shields.io/badge/Fedora-44%20%7C%20Rawhide-informational.svg)]()

Enterprise-grade automated RPM packaging and continuous delivery pipeline for **Mercury Browser** on Fedora Linux. 

This repository tracks upstream releases from [Alex313031/Mercury](https://github.com/Alex313031/Mercury), repackaging high-performance vectorized binaries for **Fedora Copr** with dedicated zero-configuration hardware video acceleration routing across NVIDIA, AMD, and Intel GPUs.

* **Copr Repository:** [universish/Mercury](https://copr.fedorainfracloud.org/coprs/universish/Mercury/)

---

## 🎯 Architecture & Mission

Mercury is a compiler-optimized web browser fork engineered to maximize hardware throughput via modern vector instruction sets.

### Key Packaging Principles
1. **Strict Architecture Filtering:** Only compiler-optimized binaries targeting **`x86_64` (AVX2 instructions enabled)** and **`aarch64` (ARM64)** are extracted and packaged. Non-vectorized x86 builds are intentionally excluded.
2. **Deterministic Fallback Pipeline:** The automation inspects upstream release assets daily, enforcing a strict package priority matrix:
   $$\text{RPM} \longrightarrow \text{DEB} \longrightarrow \text{AppImage}$$
   *(Unreliable portable ZIP archives are completely bypassed to preserve POSIX file permissions, shared library links, and system icon assets).*
3. **Automated Lifecycle & Release Counter:** The workflow checks upstream every day at **23:30 Europe/Istanbul** and tracks release versions and packaging revision numbers in `state.json` (e.g., `<version>-1` $\rightarrow$ `<version>-2`).
4. **Targeted Distributions:** The GitHub hosted VM prepares and scans the payloads in a Fedora container. Copr then repackages the approved SRPM for the targets in [`copr-chroots.txt`](copr-chroots.txt): AlmaLinux / Alma+EPEL 9 and 10, Kitten 10 variants, CentOS Stream 8/9/10 and EPEL Next 8/9, EPEL 7/8/9/10, Fedora 44/45/ELN/Rawhide, openSUSE Leap 16.0/Tumbleweed, RHEL 7/8/9/10 and RHEL+EPEL 10, plus Custom 1 x86_64. Requested x86_64_v2 chroots reuse the x86_64 AVX2 payload; AVX2 remains a CPU requirement beyond the v2 baseline. Custom 1 i386 is recorded but skipped with an Actions warning because the selected upstream payloads are 64 bit only. Custom chroots require usable repository/buildroot configuration in Copr. Successful packaging does not establish runtime ABI compatibility on older distributions.

---

## ⚡ Runtime Engine & Acceleration Parameters

Mercury is built on the **Mozilla Gecko** engine. Standard Chromium command-line switches (e.g., `--ozone-platform`, `--use-gl=angle`, `--enable-features`) do not apply to Gecko. 

To deliver out-of-the-box hardware video acceleration (VA-API/NVDEC) and solve standard Linux display server regressions, the package applies the following runtime routing:

### 1. Smart Launcher Environment Variables (`mercury-launcher.sh`)

| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `LIBVA_DRIVER_NAME` | `nvidia` | Directs VA-API calls to the `nvidia-vaapi-driver` backend. |
| `NVD_BACKEND` | `direct` | Forces direct NVDEC surface presentation bypassing OpenGL interop bottlenecks. |
| `__NV_PRIME_RENDER_OFFLOAD` | `1` | Enables hybrid graphics rendering offload to the NVIDIA discrete GPU. |
| `__GLX_VENDOR_LIBRARY_NAME` | `nvidia` | Selects NVIDIA proprietary GLX/EGL vendor ICD libraries. |
| `MOZ_DISABLE_RDD_SANDBOX` | `1` | **Critical for NVIDIA:** Allows the Gecko RDD process to access NVIDIA proprietary driver modules and DRM nodes. |
| `MOZ_ENABLE_WAYLAND` | `1` | Forces native Wayland client surface integration on GNOME/KDE. |

### 2. Pre-Configured Preferences (`defaults/pref/gpu-acceleration.js`)

Installed globally at `/opt/mercury-browser/defaults/pref/gpu-acceleration.js` to ensure zero manual intervention:

```javascript
// Hardware video acceleration via VA-API / FFmpeg
pref("media.ffmpeg.vaapi.enabled", true);
pref("media.rdd-ffmpeg.enabled", true);

// Bypasses Mozilla's hardcoded Linux NVIDIA blocklist (FEATURE_HARDWARE_VIDEO_DECODING_NO_LINUX_NVIDIA)
pref("media.hardware-video-decoding.force-enabled", true);

// Direct DMA-BUF memory sharing and EGL pipeline enablement
pref("widget.dmabuf.force-enabled", true);
pref("gfx.x11-egl.force-enabled", true);

```
### 3. GNOME Shell & Wayland Desktop Integration

* **Window Grouping & Taskbar Pinning:** Wayland identifies the root client as `mercury-default`. The `.desktop` file explicitly declares:
```ini
StartupWMClass=mercury-default

```

---

## 🚀 Installation Guide

### 1. Enable the Copr Repository
```bash
sudo dnf copr enable universish/Mercury

```

### 2. Install Mercury Browser

```bash
sudo dnf install -y mercury-browser
```

This eliminates detached, duplicate, or unassigned blank icons on the GNOME Dash/Dock.
* **Multi-Scale Icon Deployment:** Extracts native Firefox application icons directly from `/opt/mercury-browser/browser/chrome/icons/default/` into system hicolor directories (`16x16`, `32x32`, `48x48`, `64x64`, `128x128`).


## 🔄 Updating Packages

To bypass local metadata caching and immediately pull new builds or packaging revisions:

```bash
sudo dnf upgrade --refresh "mercury*" "mercury-browser*"

```

If package metadata does not resolve immediately:

```bash
sudo dnf clean all && sudo dnf makecache
sudo dnf install -y mercury-browser

```

---

## 🗑️ Removal & Cleanup

### Remove Package

```bash
sudo dnf remove -y mercury-browser

```

### Disable or Purge Copr Repository

```bash
# Temporarily disable
sudo dnf copr disable universish/Mercury

# Completely remove repository configuration
sudo dnf copr remove universish/Mercury

```

### Optional: Purge User Data

```bash
rm -rf ~/.config/mercury-flags.conf ~/.config/mercury

```

---

## 🛡️ Security & Integrity

* **Non-Invasive RPM Spec:** Packages isolate core binaries inside `/opt/mercury-browser/` without overriding base system shared libraries.
* **Hermetic Packaging:** All artifacts are assembled in official Fedora root containers and submitted to isolated chroots on Fedora Copr.
* **GitHub Actions security gate:** Before the SRPM is uploaded or submitted to Copr, the extracted x86_64 and aarch64 payloads must pass static integrity checks and a full recursive ClamAV scan with freshly downloaded signatures. These steps run in the GitHub hosted Actions job, not on Copr workers. A failed check stops publication.
* **Optional VirusTotal:** Add `VT_API_KEY` as a GitHub Actions repository secret to enable it. The workflow never uploads the payload or an archive: it calculates SHA-256 hex digests and queries each unique extracted file individually. A hash lookup only checks files already known to VirusTotal; it does not upload or newly scan the file. To respect the public API rate limit, calls are spaced 16 seconds apart. A malicious or suspicious result stops publication. Missing credentials, quota, network, timeout, malformed responses, and unknown-hash cases emit Actions warnings and leave the mandatory ClamAV and static gates in control.
* **License:** This packaging automation infrastructure is distributed under the [MIT License](https://github.com/Alex313031/Mercury/blob/main/LICENSE.md).
* **Mercury Browser License:** [Mozilla Public License 2.0](https://github.com/universish/Mercury..Browser..Copr..CI/blob/main/LICENSE.md)
* Mercury Browser remains governed by its respective upstream licenses (BSD-3-Clause / Chromium Authors).

