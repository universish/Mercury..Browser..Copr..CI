#!/usr/bin/env bash
set -e

# 1. ~/.config/mercury-flags.conf otomatik yapılandırma denetimi[cite: 1]
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}"
FLAGS_FILE="$CONFIG_DIR/mercury-flags.conf"
SYSTEM_FLAGS="/etc/mercury/mercury-flags.conf"

if [ ! -f "$FLAGS_FILE" ]; then
    mkdir -p "$CONFIG_DIR"
    if [ -f "$SYSTEM_FLAGS" ]; then
        cp "$SYSTEM_FLAGS" "$FLAGS_FILE"
    else
        cat << 'EOF' > "$FLAGS_FILE"
--ozone-platform=x11
--enable-features=VaapiVideoDecodeLinuxGL,VaapiVideoEncoderLinuxGL
--ignore-gpu-blocklist
--enable-zero-copy
--use-gl=angle
--use-angle=gl
EOF
    fi
fi

# 2. Donanım ve GPU Tanılama (NVIDIA Offload ve VA-API Entegrasyonu)[cite: 1]
if [ -e /dev/nvidia0 ] || [ -e /proc/driver/nvidia ] || command -v nvidia-smi >/dev/null 2>&1; then
    export NVD_BACKEND="${NVD_BACKEND:-direct}"
    export __NV_PRIME_RENDER_OFFLOAD="${__NV_PRIME_RENDER_OFFLOAD:-1}"
    export __GLX_VENDOR_LIBRARY_NAME="${__GLX_VENDOR_LIBRARY_NAME:-nvidia}"
fi

# 3. Bayrakları çözümle[cite: 1]
USER_FLAGS=()
if [ -f "$FLAGS_FILE" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        line="$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        [[ -z "$line" || "$line" =~ ^# ]] && continue
        USER_FLAGS+=("$line")
    done < "$FLAGS_FILE"
fi

# 4. İkili dosyayı çalıştır[cite: 1]
if [ -x /opt/mercury-browser/mercury ]; then
    exec /opt/mercury-browser/mercury "${USER_FLAGS[@]}" "$@"
elif [ -x /opt/mercury-browser/mercury-browser ]; then
    exec /opt/mercury-browser/mercury-browser "${USER_FLAGS[@]}" "$@"
else
    echo "Hata: Mercury çalıştırılabilir ikili dosyası bulunamadı." >&2
    exit 1
fi
