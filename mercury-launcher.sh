#!/usr/bin/env bash
set -e

# NVIDIA Donanım ve VA-API Hızlandırma Değişkenleri
if [ -e /dev/nvidia0 ] || [ -e /proc/driver/nvidia ] || command -v nvidia-smi >/dev/null 2>&1; then
    export LIBVA_DRIVER_NAME=nvidia
    export NVD_BACKEND="${NVD_BACKEND:-direct}"
    export __NV_PRIME_RENDER_OFFLOAD="${__NV_PRIME_RENDER_OFFLOAD:-1}"
    export __GLX_VENDOR_LIBRARY_NAME="${__GLX_VENDOR_LIBRARY_NAME:-nvidia}"
    # Firefox'un NVIDIA VA-API kütüphanesine erişebilmesi için gereklidir
    export MOZ_DISABLE_RDD_SANDBOX=1
fi

# Yerel Wayland Desteği
export MOZ_ENABLE_WAYLAND=1

# İkili dosyayı çalıştır
if [ -x /opt/mercury-browser/mercury ]; then
    exec /opt/mercury-browser/mercury "$@"
elif [ -x /opt/mercury-browser/mercury-bin ]; then
    exec /opt/mercury-browser/mercury-bin "$@"
else
    echo "Hata: Mercury ikili dosyası bulunamadı." >&2
    exit 1
fi
