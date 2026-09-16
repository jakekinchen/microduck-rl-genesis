"""Complete snapshot bytes must survive deduplication and reject tampering."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest

from experiments.walking.snapshots_v43 import CHUNK, MAX_BYTES, store_bytes, load_bytes


class SnapshotTests(unittest.TestCase):
    def test_shared_blocks_preserve_every_byte(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); blobs = root / "blobs"
            common = bytes(range(256)) * (CHUNK // 256)
            first, second = common + b"first state", common + b"second state"
            store_bytes(first, root / "a.json", blobs)
            store_bytes(second, root / "b.json", blobs)
            self.assertEqual(load_bytes(root / "a.json", blobs), first)
            self.assertEqual(load_bytes(root / "b.json", blobs), second)
            self.assertEqual(len(list(blobs.iterdir())), 3)

    def test_changed_block_cannot_reconstruct(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); blobs = root / "blobs"
            record = store_bytes(b"trusted state", root / "a.json", blobs)
            (blobs / (record["chunks"][0] + ".gz")).write_bytes(gzip.compress(b"changed state"))
            with self.assertRaisesRegex(ValueError, "corruption"):
                load_bytes(root / "a.json", blobs)

    def test_index_cannot_expand_read_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); path = root / "a.json"
            record = store_bytes(b"state", path, root / "blobs")
            record["bytes"] = MAX_BYTES + 1
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "index"):
                load_bytes(path, root / "blobs")


if __name__ == "__main__":
    unittest.main()
