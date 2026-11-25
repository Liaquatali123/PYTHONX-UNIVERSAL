import base64
import tempfile
import unittest
import zipfile
from pathlib import Path
from pythonx.scanner import inspect_file, scan_path
from pythonx.recovery import decode_payload, extract_zip, recover_path

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def test_source_inspection(self):
        p = self.root / "a.py"
        p.write_text("print('ok')\n")
        self.assertTrue(inspect_file(p)["syntax_valid"])
    def test_directory_scan(self):
        (self.root / "a.py").write_text("x=1")
        self.assertEqual(len(scan_path(self.root)), 1)
    def test_zip_extract(self):
        z = self.root / "a.zip"
        with zipfile.ZipFile(z, "w") as f:
            f.writestr("folder/a.txt", "hello")
        out = self.root / "out"
        self.assertEqual(len(extract_zip(z, out)), 1)
        self.assertEqual((out / "folder/a.txt").read_text(), "hello")
    def test_zip_traversal_rejected(self):
        z = self.root / "bad.zip"
        with zipfile.ZipFile(z, "w") as f:
            f.writestr("../escape.txt", "no")
        with self.assertRaises(ValueError):
            extract_zip(z, self.root / "out")
    def test_base64(self):
        p = self.root / "payload"
        p.write_bytes(base64.b64encode(b"decoded"))
        out = self.root / "out.bin"
        self.assertEqual(decode_payload(p, out), "base64")
        self.assertEqual(out.read_bytes(), b"decoded")
    def test_recover_source(self):
        p = self.root / "script.py"
        p.write_text("x=42")
        result = recover_path(p, self.root / "out")
        self.assertEqual(Path(result[0]).read_text(), "x=42")

if __name__ == "__main__":
    unittest.main()
