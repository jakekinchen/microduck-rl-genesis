#!/usr/bin/env python3
"""Check Git receipt bytes and catalog references without downloading bulk evidence."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def catalog(root):
    directory = root / 'docs/workspace/publication-20260916'
    archive = json.loads((directory / 'archive.json').read_text())
    path = directory / 'files.jsonl.gz'
    if sha(path) != archive['catalog_sha256']:
        raise ValueError('Publication catalog checksum mismatch')
    with gzip.open(path, 'rt') as stream:
        rows = [json.loads(line) for line in stream]
    result = {r['path']: r['sha256'] for r in rows}
    if len(result) != len(rows) or len(rows) != archive['files']:
        raise ValueError('Duplicate or missing catalog entries')
    return result


def check_manifests(root, tracked, archived):
    counts = {'manifests': 0, 'git_byte_checks': 0, 'archive_reference_checks': 0}
    cached = {}
    for manifest in sorted(p for p in tracked if p.startswith('receipts/') and p.endswith('/SHA256SUMS')):
        counts['manifests'] += 1
        for line in (root / manifest).read_text().splitlines():
            if not line.strip():
                continue
            match = re.fullmatch(r'([a-f0-9]{64}) [ *](.+)', line)
            if not match:
                raise ValueError(f'Invalid manifest line in {manifest}')
            expected, relative = match.groups()
            if PurePosixPath(relative).is_absolute():
                raise ValueError(f'Absolute manifest path in {manifest}')
            path = posixpath.normpath(posixpath.join(posixpath.dirname(manifest), relative))
            if path == '..' or path.startswith('../'):
                raise ValueError(f'Manifest path escapes repository: {manifest}')
            if path in tracked:
                target = root / path
                if target.is_symlink() or not target.is_file():
                    raise ValueError(f'Tracked payload missing or symlinked: {path}')
                if path not in cached:
                    cached[path] = sha(target)
                actual = cached[path]
                counts['git_byte_checks'] += 1
            else:
                actual = archived.get(path)
                counts['archive_reference_checks'] += 1
            if actual != expected:
                raise ValueError(f'Receipt hash missing or mismatched: {path}')
    return counts


def check_whitespace(root, base):
    path = root / 'docs/workspace/publication-20260916/immutable-formatting.json'
    exemptions = json.loads(path.read_text())
    exclusions = []
    for row in exemptions:
        relative = PurePosixPath(row['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe immutable-formatting path')
        target = root / relative
        if target.is_symlink() or sha(target) != row['sha256']:
            raise ValueError(f'Immutable formatting payload changed: {relative}')
        exclusions.append(f':(exclude,literal){relative}')
    subprocess.run(['git', 'diff', '--check', f'{base}...HEAD', '--', '.', *exclusions],
                   cwd=root, check=True)
    return len(exemptions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--whitespace-base')
    parser.add_argument('--json-out', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')) - {''}
    report = check_manifests(root, tracked, catalog(root))
    if args.whitespace_base:
        report['hash_bound_formatting_exemptions'] = check_whitespace(root, args.whitespace_base)
    report['status'] = 'passed'
    report['boundary'] = 'Git payload bytes verified; archive-only references matched to the catalog. Bulk payloads are not downloaded or reverified by this CI check.'
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
