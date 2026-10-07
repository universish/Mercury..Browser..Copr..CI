# Mercury Browser (AVX2 & ARM64) for Fedora Copr

[![Fedora Copr](https://img.shields.io/badge/Copr-universish%2FMercury-blue.svg)](https://copr.fedorainfracloud.org/coprs/universish/Mercury/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Arch-x86__64%20(AVX2)%20%7C%20aarch64-brightgreen.svg)]()
[![Target OS](https://img.shields.io/badge/Fedora-44%20%7C%20Rawhide-informational.svg)]()

Enterprise-grade, automated RPM packaging and continuous delivery pipeline for **Mercury Browser** on Fedora Linux. 

This repository synchronizes upstream releases from [Alex313031/Mercury](https://github.com/Alex313031/Mercury), repackaging optimized binaries for **Fedora Copr** with specialized GPU runtime routing and hardware video acceleration.

---

## 🎯 Architecture & Mission

Mercury is an aggressive compiler-optimized fork of Chromium, engineered to extract peak computing throughput via modern CPU instruction sets.

This packaging project fulfills the need for native system integration on modern Fedora environments with zero manual intervention:

1. **Strict Architecture Filtering:** Only compiler-optimized binaries targeting **`x86_64` (AVX2-enabled processors)** and **`aarch64` (ARM64)** are extracted and packaged. Non-vectorized architectures are omitted to maintain performance integrity.
2. **Deterministic Fallback Pipeline:** The automation scans upstream releases twice daily, following an exact priority tree:
   $$\text{RPM} \longrightarrow \text{Portable (ZIP/TAR)} \longrightarrow \text{DEB} \longrightarrow \text{AppImage}$$
3. **Automated Version & Release Tracking:** Every build increment is tracked deterministically in `state.json`, ensuring clean version bumping (e.g., `<version>-1` $\rightarrow$ `<version>-2`).
4. **Intelligent Multi-GPU Hardware Routing:**
   - **NVIDIA GPU Detection:** Automatically injects `NVD_BACKEND=direct`, `__NV_PRIME_RENDER_OFFLOAD=1`, and `__GLX_VENDOR_LIBRARY_NAME=nvidia` alongside ANGLE/OpenGL interop flags.
   - **Mesa Native Fallback:** Retains standard Mesa/VA-API acceleration pipelines on Intel and AMD configurations.

---

## 🚀 Installation Guide

### 1. Enable the Copr Repository
```bash
sudo dnf copr enable universish/Mercury
