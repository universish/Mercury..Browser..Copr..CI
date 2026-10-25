#!/usr/bin/env python3
"""Fail packaging if an extracted upstream payload breaks basic integrity rules."""

import os
import stat
import struct
import sys
from pathlib import Path


MACHINES = {"x86_64": 62, "aarch64": 183}
REQUIRED = {"application.ini", "omni.ja", "libxul.so"}


def check(root: Path, arch: str) -> list[str]:
    errors: list[str] = []
    if arch not in MACHINES or not root.is_dir():
        return [f"{root}: geçersiz dizin veya mimari: {arch}"]

    root = root.resolve()
    names: set[str] = set()
    regular_count = 0
    elf_count = 0

    for current, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(current) / name
            mode = path.lstat().st_mode
            names.add(name)
            if stat.S_ISLNK(mode):
                resolved = path.resolve()
                if not resolved.is_relative_to(root) or not resolved.exists():
                    errors.append(f"{path}: bozuk veya payload dışına çıkan sembolik bağ")
                continue
            if stat.S_ISDIR(mode):
                if mode & 0o022:
                    errors.append(f"{path}: grup/dünya tarafından yazılabilir dizin")
                continue
            if not stat.S_ISREG(mode):
                errors.append(f"{path}: özel dosya türüne izin verilmiyor")
                continue
            regular_count += 1
            if mode & 0o6022:
                errors.append(f"{path}: setuid/setgid veya grup/dünya yazma izni")
            if path.stat().st_size > 2_000_000_000:
                errors.append(f"{path}: ClamAV 2000M dosya sınırını aşıyor")

            with path.open("rb") as stream:
                header = stream.read(20)
            if header[:4] == b"\x7fELF":
                elf_count += 1
                if len(header) < 20 or header[5] not in (1, 2):
                    errors.append(f"{path}: geçersiz ELF başlığı")
                    continue
                byte_order = "<" if header[5] == 1 else ">"
                machine = struct.unpack_from(byte_order + "H", header, 18)[0]
                if machine != MACHINES[arch]:
                    errors.append(f"{path}: beklenmeyen ELF mimarisi ({machine})")

    missing = REQUIRED - names
    if missing:
        errors.append(f"{root}: Gecko çekirdeği eksik: {', '.join(sorted(missing))}")
    if not ({"mercury", "mercury-bin"} & names):
        errors.append(f"{root}: Mercury çalıştırılabilir dosyası eksik")
    if not regular_count or not elf_count:
        errors.append(f"{root}: düzenli dosya veya ELF ikilisi bulunamadı")
    print(f"{root}: {regular_count} dosya, {elf_count} ELF, {len(errors)} hata")
    return errors


def main() -> int:
    errors: list[str] = []
    for arg in sys.argv[1:]:
        if ":" not in arg:
            errors.append(f"Geçersiz argüman: {arg}")
            continue
        root, arch = arg.rsplit(":", 1)
        errors.extend(check(Path(root), arch))
    if not sys.argv[1:]:
        errors.append("Taranacak payload belirtilmedi")
    for error in errors:
        print(f"::error::{error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
