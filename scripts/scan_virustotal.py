#!/usr/bin/env python3
"""Best-effort VirusTotal gate; ClamAV and static checks remain mandatory."""

import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


BASE = "https://www.virustotal.com/api/v3"
MAX_UPLOAD = 650 * 1024 * 1024
DIRECT_UPLOAD = 32 * 1024 * 1024
MAX_REQUESTS = 40  # Reserve most of a public key's daily quota.
REQUEST_INTERVAL = 16  # At most 4 calls per minute.


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

    def request(self, method: str, url: str, body=None, content_type=None):
        if self.calls >= MAX_REQUESTS:
            raise VTError(f"İstek bütçesi doldu ({MAX_REQUESTS})")
        elapsed = time.monotonic() - self.last_call
        if self.calls and elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)
        self.calls += 1
        self.last_call = time.monotonic()
        headers = {"x-apikey": self.key, "accept": "application/json"}
        if content_type:
            headers["content-type"] = content_type
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return 404, None
            raise VTError(f"HTTP {error.code}", error.code) from error
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as error:
            raise VTError(str(error)) from error

    def upload(self, path: Path):
        size = path.stat().st_size
        if size > MAX_UPLOAD:
            raise VTError(f"{path.name}: 650 MB yükleme sınırını aşıyor")
        url = f"{BASE}/files"
        if size > DIRECT_UPLOAD:
            status, response = self.request("GET", f"{BASE}/files/upload_url")
            url = response.get("data", "") if status == 200 else ""
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme != "https" or parsed.hostname != "www.virustotal.com":
                raise VTError("Geçersiz büyük dosya yükleme adresi")
        boundary = "mercury-vt-upload-boundary"
        prefix = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                  f"filename=\"{path.name}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode()
        suffix = f"\r\n--{boundary}--\r\n".encode()
        # The GitHub hosted runner has enough memory for the API's 650 MB maximum.
        body = prefix + path.read_bytes() + suffix
        status, response = self.request("POST", url, body, f"multipart/form-data; boundary={boundary}")
        analysis_id = response.get("data", {}).get("id") if status == 200 else None
        if not analysis_id:
            raise VTError("Yükleme yanıtında analiz kimliği yok")
        return analysis_id

    def await_analysis(self, analysis_id: str, label: str):
        for _ in range(6):
            status, response = self.request("GET", f"{BASE}/analyses/{urllib.parse.quote(analysis_id, safe='')}")
            if status != 200:
                raise VTError(f"{label}: analiz alınamadı (HTTP {status})")
            attributes = response.get("data", {}).get("attributes", {})
            if attributes.get("status") == "completed":
                check_stats(attributes.get("stats", {}), label)
                print(f"VirusTotal: {label} analizi tamamlandı")
                return
        raise VTError(f"{label}: analiz zamanında tamamlanmadı")

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
            status, response = self.request("GET", f"{BASE}/files/{digest}")
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


def compressed_fallback(root: Path, target: Path):
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file() and not path.is_symlink():
                archive.write(path, path.relative_to(root))


def main():
    if len(sys.argv) < 2:
        warn("Taranacak arşiv belirtilmedi")
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
        filename, dirname = item.split(":", 1)
        source, root = Path(filename), Path(dirname)
        if not source.is_file() or not root.is_dir():
            warn(f"{filename}/{dirname}: dosya veya payload bulunamadı")
            continue

        try:
            client.await_analysis(client.upload(source), source.name)
            continue
        except Detection:
            raise
        except VTError as error:
            warn(f"{source.name}: doğrudan yükleme/analiz başarısız: {error}")
            if error.status == 429 or client.calls >= MAX_REQUESTS:
                break

        with tempfile.TemporaryDirectory(prefix="mercury-vt-") as folder:
            zipped = Path(folder) / f"{root.name}.zip"
            try:
                compressed_fallback(root, zipped)
                client.await_analysis(client.upload(zipped), zipped.name)
                continue
            except Detection:
                raise
            except (VTError, OSError, zipfile.BadZipFile) as error:
                warn(f"{root}: sıkıştırılmış yükleme/analiz başarısız: {error}")
                if isinstance(error, VTError) and error.status == 429:
                    break

        try:
            client.query_hashes(root)
        except Detection:
            raise
        except (VTError, OSError) as error:
            warn(f"{root}: SHA-256 sorguları tamamlanamadı: {error}")
            if isinstance(error, VTError) and (error.status == 429 or client.calls >= MAX_REQUESTS):
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
