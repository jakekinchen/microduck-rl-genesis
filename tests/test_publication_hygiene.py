import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_published_receipts import check_manifests


class PublishedReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / 'receipts/run'
        self.directory.mkdir(parents=True)
        self.payload = b'independent known payload\n'
        self.digest = hashlib.sha256(self.payload).hexdigest()
        self.manifest = 'receipts/run/SHA256SUMS'
        self.path = 'receipts/run/payload.txt'
        (self.root / self.manifest).write_text(f'{self.digest}  payload.txt\n')

    def test_git_bytes_are_verified_even_when_catalog_matches(self):
        (self.root / self.path).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'mismatched'):
            check_manifests(self.root, {self.manifest, self.path}, {self.path: self.digest})

    def test_valid_git_payload_is_counted_as_byte_check(self):
        (self.root / self.path).write_bytes(self.payload)
        result = check_manifests(self.root, {self.manifest, self.path}, {})
        self.assertEqual(result['git_byte_checks'], 1)
        self.assertEqual(result['archive_reference_checks'], 0)

    def test_archive_match_is_explicitly_not_a_local_byte_check(self):
        result = check_manifests(self.root, {self.manifest}, {self.path: self.digest})
        self.assertEqual(result['git_byte_checks'], 0)
        self.assertEqual(result['archive_reference_checks'], 1)

    def test_missing_or_wrong_archive_hash_fails(self):
        for archived in [{}, {self.path: '0' * 64}]:
            with self.subTest(archived=archived), self.assertRaises(ValueError):
                check_manifests(self.root, {self.manifest}, archived)

    def test_missing_tracked_payload_cannot_fall_back_to_archive(self):
        with self.assertRaisesRegex(ValueError, 'Tracked payload missing'):
            check_manifests(self.root, {self.manifest, self.path}, {self.path: self.digest})

    def test_manifest_cannot_escape_repository(self):
        (self.root / self.manifest).write_text(f'{self.digest}  ../../../outside\n')
        with self.assertRaisesRegex(ValueError, 'escapes repository'):
            check_manifests(self.root, {self.manifest}, {})


if __name__ == '__main__':
    unittest.main()
