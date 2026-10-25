import importlib.util
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


payload = load("check_payload", "check_payload.py")
vt = load("scan_virustotal", "scan_virustotal.py")


class SecurityGateTests(unittest.TestCase):
    def make_payload(self, root, machine=62):
        for name in ("application.ini", "omni.ja"):
            (root / name).write_bytes(b"sample")
        header = bytearray(20)
        header[:4] = b"\x7fELF"
        header[5] = 1
        struct.pack_into("<H", header, 18, machine)
        (root / "libxul.so").write_bytes(header)
        binary = root / "mercury"
        binary.write_bytes(header)
        binary.chmod(0o755)

    def test_static_gate_accepts_expected_architecture(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.make_payload(root)
            self.assertEqual(payload.check(root, "x86_64"), [])

    def test_static_gate_rejects_wrong_architecture_and_escaping_link(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "payload"
            root.mkdir()
            self.make_payload(root, machine=183)
            (root / "outside").symlink_to("../../elsewhere")
            errors = payload.check(root, "x86_64")
            self.assertTrue(any("ELF mimarisi" in error for error in errors))
            self.assertTrue(any("payload dışına" in error for error in errors))

    def test_virustotal_detections_block_publication(self):
        with self.assertRaises(vt.Detection):
            vt.check_stats({"malicious": 1, "suspicious": 0}, "sample")

    def test_virustotal_retries_zip_then_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "payload"
            root.mkdir()
            (root / "sample").write_bytes(b"sample")
            archive = Path(folder) / "payload.tar.gz"
            archive.write_bytes(b"archive")
            observed = []

            def fail_upload(client, path):
                observed.append(path.suffix)
                raise vt.VTError("simulated upload error")

            with patch.dict(os.environ, {"VT_API_KEY": "test-key"}), \
                 patch.object(vt.sys, "argv", ["script", f"{archive}:{root}"]), \
                 patch.object(vt.Client, "upload", fail_upload), \
                 patch.object(vt.Client, "query_hashes", lambda client, path: observed.append("hashes")):
                self.assertEqual(vt.main(), 0)
            self.assertEqual(observed, [".gz", ".zip", "hashes"])


if __name__ == "__main__":
    unittest.main()
