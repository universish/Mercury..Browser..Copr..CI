# Mercury Browser (AVX2 & ARM64) for Fedora Copr

[![Fedora Copr](https://img.shields.io/badge/Copr-universish%2FMercury-blue.svg)](https://copr.fedorainfracloud.org/coprs/universish/Mercury/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Arch-x86__64%20(AVX2)%20%7C%20aarch64-brightgreen.svg)]()
[![Target OS](https://img.shields.io/badge/Fedora-44%20%7C%20Rawhide-informational.svg)]()

Enterprise-grade, automated RPM packaging and continuous delivery pipeline for **Mercury Browser** on Fedora Linux. 

This repository synchronizes upstream releases from [Alex313031/Mercury](https://github.com/Alex313031/Mercury), repackaging optimized binaries for **Fedora Copr** with specialized GPU runtime routing and hardware video acceleration.

---

## 🎯 Architecture & Mission

Mercury delivers peak computational throughput via compiler-level optimizations (AVX2 instructions on modern x86_64, NEON on ARM64).

This packaging pipeline provides:
1. **Strict Architecture Filtering:** Only compiler-optimized binaries targeting **`x86_64` (AVX2-enabled processors)** and **`aarch64` (ARM64)** are extracted and packaged. Non-vectorized builds are strictly excluded.
2. **Deterministic Fallback Pipeline:** The automation scans upstream releases twice daily, strictly enforcing package hierarchy:
   $$\text{RPM} \longrightarrow \text{DEB} \longrightarrow \text{AppImage}$$
3. **Automated Version & Release Tracking:** Every build increment is tracked deterministically in `state.json`, ensuring clean version bumping (e.g., `<version>-1` $\rightarrow$ `<version>-2`).

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
