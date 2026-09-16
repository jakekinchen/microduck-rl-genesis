"""Deduplicate trusted local MuJoCo snapshots without dropping state fields."""
import gzip
import hashlib
import json
from pathlib import Path
import pickle
import re

CHUNK = 65536
MAX_BYTES = 256 * 1024 * 1024


def store_bytes(payload, path, blob_directory):
    if not 0 < len(payload) <= MAX_BYTES:
        raise ValueError("snapshot size outside bounded contract")
    path, blob_directory = Path(path), Path(blob_directory)
    blob_directory.mkdir(parents=True, exist_ok=True)
    chunks = []
    for offset in range(0, len(payload), CHUNK):
        block = payload[offset:offset + CHUNK]
        sha = hashlib.sha256(block).hexdigest()
        target = blob_directory / (sha + ".gz")
        if not target.exists():
            with target.open("xb") as stream:
                stream.write(gzip.compress(block, compresslevel=1, mtime=0))
        chunks.append(sha)
    record = {"schema":"microduck.full-state-chunks/v43", "bytes":len(payload),
              "sha256":hashlib.sha256(payload).hexdigest(), "chunks":chunks}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(record, stream)
    return record


def load_bytes(path, blob_directory):
    record = json.loads(Path(path).read_text())
    size = record.get("bytes")
    if (record.get("schema") != "microduck.full-state-chunks/v43"
            or type(size) is not int or not 0 < size <= MAX_BYTES
            or len(record["chunks"]) != (size + CHUNK - 1) // CHUNK):
        raise ValueError("invalid snapshot index")
    payload = bytearray()
    for sha in record["chunks"]:
        if not isinstance(sha, str) or not re.fullmatch("[0-9a-f]{64}", sha):
            raise ValueError("invalid snapshot chunk identity")
        with gzip.open(Path(blob_directory) / (sha + ".gz"), "rb") as stream:
            block = stream.read(CHUNK + 1)
        if len(block) > CHUNK or hashlib.sha256(block).hexdigest() != sha:
            raise ValueError("snapshot chunk corruption")
        payload.extend(block)
    if len(payload) != size or hashlib.sha256(payload).hexdigest() != record["sha256"]:
        raise ValueError("snapshot reconstruction corruption")
    return payload


def save_state(state, path, blob_directory):
    return store_bytes(pickle.dumps(state, protocol=5), path, blob_directory)


def load_state(path, blob_directory):
    # Caller must verify the index against a trusted locally produced manifest.
    return pickle.loads(load_bytes(path, blob_directory))
