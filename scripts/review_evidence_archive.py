#!/usr/bin/env python3
"""Verify the September 16 evidence snapshot; optionally restore into an empty directory.

No simulator imports, networking, original-file edits, or policy execution.
"""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tarfile


class Parts(io.RawIOBase):
    def __init__(self, paths):
        self.paths = iter(paths)
        self.current = None

    def readable(self):
        return True

    def readinto(self, buffer):
        while True:
            if self.current is None:
                path = next(self.paths, None)
                if path is None:
                    return 0
                self.current = path.open('rb')
            n = self.current.readinto(buffer)
            if n:
                return n
            self.current.close()
            self.current = None

    def close(self):
        if self.current:
            self.current.close()
        super().close()


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parts-dir', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, default=Path(__file__).resolve().parents[1]
                        / 'docs/workspace/publication-20260916')
    parser.add_argument('--extract-to', type=Path,
                        help='Must be absent or empty; never use an existing working checkout.')
    parser.add_argument('--json-out', type=Path)
    args = parser.parse_args()
    metadata = json.loads((args.metadata / 'archive.json').read_text())
    catalog_path = args.metadata / 'files.jsonl.gz'
    if digest(catalog_path) != metadata['catalog_sha256']:
        raise ValueError('Catalog checksum mismatch')
    with gzip.open(catalog_path, 'rt') as stream:
        rows = [json.loads(line) for line in stream]
    expected = {row['path']: row for row in rows}
    if len(expected) != len(rows) or len(rows) != metadata['files']:
        raise ValueError('Catalog has duplicate/missing entries')
    for name in expected:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path) != name:
            raise ValueError(f'Unsafe catalog path: {name}')
    parts = []
    for part in metadata['parts']:
        if Path(part['name']).name != part['name']:
            raise ValueError('Unsafe part name')
        path = args.parts_dir / part['name']
        if path.stat().st_size != part['bytes'] or digest(path) != part['sha256']:
            raise ValueError(f'Part checksum mismatch: {path.name}')
        parts.append(path)
        print(f'Part verified: {path.name}', flush=True)
    output = args.extract_to
    if output:
        if output.is_symlink() or (output.exists() and (not output.is_dir() or any(output.iterdir()))):
            raise ValueError('Extraction destination must be absent or empty and not a symlink')
        output.mkdir(parents=True, exist_ok=True)
    verified = {}
    logical_bytes = 0
    with io.BufferedReader(Parts(parts)) as joined:
        with gzip.GzipFile(fileobj=joined, mode='rb') as uncompressed:
            with tarfile.open(fileobj=uncompressed, mode='r|') as archive:
                for member in archive:
                    row = expected.get(member.name)
                    if row is None or member.name in verified:
                        raise ValueError(f'Unexpected/duplicate archive member: {member.name}')
                    target = output / member.name if output else None
                    if target:
                        target.parent.mkdir(parents=True, exist_ok=True)
                    if member.islnk():
                        previous = verified.get(member.linkname)
                        if previous != (row['sha256'], row['bytes'], row['mode']):
                            raise ValueError(f'Invalid hardlink: {member.name}')
                        actual = row['sha256']
                        if target:
                            os.link(output / member.linkname, target)
                    elif member.isfile():
                        if member.size != row['bytes']:
                            raise ValueError(f'Size mismatch: {member.name}')
                        hasher = hashlib.sha256()
                        source = archive.extractfile(member)
                        dest = target.open('xb') if target else None
                        try:
                            while chunk := source.read(1024 * 1024):
                                hasher.update(chunk)
                                if dest:
                                    dest.write(chunk)
                        finally:
                            source.close()
                            if dest:
                                dest.close()
                        actual = hasher.hexdigest()
                    else:
                        raise ValueError(f'Unsupported archive member type: {member.name}')
                    if actual != row['sha256'] or member.mode != row['mode']:
                        raise ValueError(f'Content/mode mismatch: {member.name}')
                    if target:
                        target.chmod(row['mode'])
                    verified[member.name] = (actual, row['bytes'], row['mode'])
                    logical_bytes += row['bytes']
                    if len(verified) % 10000 == 0:
                        print(f'Files verified: {len(verified)}/{len(expected)}', flush=True)
            # Consume the gzip trailer as well as the tar payload.
            if uncompressed.read().strip(b'\0'):
                raise ValueError('Unexpected data after tar archive')
    if set(verified) != set(expected) or logical_bytes != metadata['logical_bytes']:
        raise ValueError('Archive/catalog coverage mismatch')
    report = {'status': 'passed', 'files_verified': len(verified),
              'logical_bytes': logical_bytes, 'parts_verified': len(parts),
              'catalog_sha256': metadata['catalog_sha256'],
              'extracted_to': str(output) if output else None,
              'claim': 'Archive integrity only; not behavior acceptance.'}
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
