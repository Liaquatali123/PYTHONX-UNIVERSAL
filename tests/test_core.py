import base64
import tempfile
import unittest
import zipfile
from pathlib import Path
from pythonx.scanner import inspect_file, scan_path
from pythonx.recovery import decode_payload, extract_zip, recover_path
from pythonx.encryption import encrypt_file, decrypt_file, is_pyx_encrypted, detect_protection

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
    def test_single_file_only(self):
        p = self.root / "a.py"
        p.write_text("x=1")
        self.assertEqual(len(scan_path(p)), 1)
        with self.assertRaises(ValueError):
            scan_path(self.root)
        with self.assertRaises(ValueError):
            recover_path(self.root, self.root / "out")
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
    def test_encrypt_decrypt_roundtrip(self):
        original = self.root / "secret.py"
        original.write_text("print('protected')\n")
        encrypted = self.root / "secret.pyx"
        restored = self.root / "restored.py"
        encrypt_file(original, encrypted, "correct horse battery")
        self.assertTrue(is_pyx_encrypted(encrypted))
        self.assertTrue(detect_protection(encrypted)["decryptable_by_pythonx"])
        decrypt_file(encrypted, restored, "correct horse battery")
        self.assertEqual(restored.read_bytes(), original.read_bytes())
    def test_wrong_password_rejected(self):
        original = self.root / "secret.py"
        original.write_text("secret")
        encrypted = self.root / "secret.pyx"
        encrypt_file(original, encrypted, "correct horse battery")
        with self.assertRaises(ValueError):
            decrypt_file(encrypted, self.root / "bad.py", "wrong password")
    def test_encryption_requires_password_length(self):
        original = self.root / "x.py"
        original.write_text("x")
        with self.assertRaises(ValueError):
            encrypt_file(original, self.root / "x.pyx", "short")

if __name__ == "__main__":
    unittest.main()
