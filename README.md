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
2. **Deterministic Fallback Pipeline:** The automation inspects upstream release assets twice daily, enforcing a strict package priority matrix:
   $$\text{RPM} \longrightarrow \text{DEB} \longrightarrow \text{AppImage}$$
   *(Unreliable portable ZIP archives are completely bypassed to preserve POSIX file permissions, shared library links, and system icon assets).*
3. **Automated Lifecycle & Release Counter:** The workflow tracks release versions and packaging revision numbers deterministically in `state.json` (e.g., `<version>-1` $\rightarrow$ `<version>-2`).
4. **Targeted Distributions:** Built specifically inside Fedora containers targeting **Fedora 44** and **Fedora Rawhide** mock chroots.

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
* **License:** This packaging automation infrastructure is distributed under the [MIT License](https://github.com/Alex313031/Mercury/blob/main/LICENSE.md).
* **Mercury Browser License:** [Mozilla Public License 2.0](https://github.com/universish/Mercury..Browser..Copr..CI/blob/main/LICENSE.md)
* Mercury Browser remains governed by its respective upstream licenses (BSD-3-Clause / Chromium Authors).

