#!/usr/bin/env python3
"""Best-effort VirusTotal hash lookup gate; mandatory local gates remain decisive."""

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE = "https://www.virustotal.com/api/v3"
REQUEST_INTERVAL = 16  # At most 4 public-API requests per minute.


class VTError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class Detection(Exception):
    pass


class Client:
    def __init__(self, key: str):
        self.key = key
        self.calls = 0
        self.last_call = 0.0

    def request(self, url: str):
        elapsed = time.monotonic() - self.last_call
        if self.calls and elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)
        self.calls += 1
        self.last_call = time.monotonic()
        request = urllib.request.Request(
            url, headers={"x-apikey": self.key, "accept": "application/json"}, method="GET"
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return 404, None
            raise VTError(f"HTTP {error.code}", error.code) from error
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as error:
            raise VTError(str(error)) from error

    def query_hashes(self, root: Path):
        seen = set()
        known = unknown = 0
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            status, response = self.request(f"{BASE}/files/{digest}")
            if status == 404:
                unknown += 1
                continue
            check_stats(response.get("data", {}).get("attributes", {}).get("last_analysis_stats", {}), str(path))
            known += 1
        print(f"VirusTotal: {root} için {known} bilinen, {unknown} bilinmeyen SHA-256 sorgulandı")
        if unknown:
            warn(f"{root}: {unknown} hash VirusTotal'da yok; hash sorgusu yeni tarama başlatmaz")


def check_stats(stats, label):
    if not isinstance(stats, dict) or "malicious" not in stats or "suspicious" not in stats:
        raise VTError(f"{label}: analiz sonucu eksik")
    if int(stats.get("malicious", 0)) or int(stats.get("suspicious", 0)):
        raise Detection(f"{label}: kötü amaçlı/şüpheli VirusTotal tespiti: {stats}")


def warn(message: str):
    print(f"::warning::VirusTotal adımı atlandı/eksik: {message}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        warn("Taranacak payload belirtilmedi")
        return 0
    key = os.environ.get("VT_API_KEY", "")
    if not key:
        warn("VT_API_KEY sırrı tanımlanmamış")
        return 0
    client = Client(key)
    for item in sys.argv[1:]:
        if ":" not in item:
            warn(f"Geçersiz argüman: {item}")
            continue
        _archive, dirname = item.split(":", 1)
        root = Path(dirname)
        if not root.is_dir():
            warn(f"{dirname}: payload bulunamadı")
            continue
        try:
            client.query_hashes(root)
        except Detection:
            raise
        except (VTError, OSError) as error:
            warn(f"{root}: SHA-256 sorguları tamamlanamadı: {error}")
            if isinstance(error, VTError) and error.status == 429:
                break
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Detection as error:
        print(f"::error::VirusTotal yayın engeli: {error}", file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        warn(f"beklenmeyen VirusTotal hatası: {type(error).__name__}: {error}")
        sys.exit(0)
