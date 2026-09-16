import collections
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path.cwd()
OUT = Path('/Volumes/cerebro-old/CodexOffload/MicroDuck/publication-20260916')
META = ROOT / 'docs/workspace/publication-20260916'
OUT.mkdir(exist_ok=True)
META.mkdir(exist_ok=True)
ROOTS = ['experiments', 'receipts', 'outputs', 'logs']
SKIP = {'__pycache__', '.pytest_cache', '.DS_Store', 'runtime-mujoco-3.10'}
PRIVATE_PATHS = {'outputs/laser-course-20260913/compilation-before.json'}
PART_BYTES = 1024**3

def sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

class SplitWriter:
    def __init__(self):
        self.files = []
        self.stream = None
        self.position = 0
        self.chunk_position = 0
    def write(self, data):
        n = len(data)
        while data:
            if self.stream is None or self.chunk_position == PART_BYTES:
                if self.stream:
                    self.stream.close()
                path = OUT / f'evidence-20260916.tar.gz.part{len(self.files)+1:03}'
                if path.exists():
                    raise RuntimeError(f'Refusing overwrite: {path}')
                self.files.append(path)
                self.stream = path.open('wb')
                self.chunk_position = 0
            take = min(len(data), PART_BYTES - self.chunk_position)
            self.stream.write(data[:take])
            data = data[take:]
            self.position += take
            self.chunk_position += take
        return n
    def flush(self):
        if self.stream:
            self.stream.flush()
    def close(self):
        if self.stream:
            self.stream.close()

files = []
symlinks = {}
excluded = []
for root in ROOTS:
    for base, dirs, names in os.walk(ROOT/root, followlinks=True):
        for name in dirs + names:
            p = Path(base)/name
            if p.is_symlink():
                target = p.resolve(strict=True)
                if not (target.is_relative_to(ROOT) or target.is_relative_to('/Volumes/cerebro-old/CodexOffload/MicroDuck')):
                    raise RuntimeError(f'Unexpected external link: {p}')
                symlinks[str(p.relative_to(ROOT))] = os.readlink(p)
        for name in list(dirs):
            if name in SKIP or name.startswith('.'):
                excluded.append(str((Path(base)/name).relative_to(ROOT)))
                dirs.remove(name)
        for name in names:
            p = Path(base)/name
            if name in SKIP or name.startswith('.') or str(p.relative_to(ROOT)) in PRIVATE_PATHS:
                excluded.append(str(p.relative_to(ROOT)))
                continue
            if not p.is_file():
                raise RuntimeError(f'Non-file input: {p}')
            files.append(p)
files.sort()
rows = []
inode_cache = {}
prior = {}
if (META/'files.jsonl.gz').exists():
    with gzip.open(META/'files.jsonl.gz', 'rt') as f:
        prior = {r['path']: r for r in map(json.loads, f)}
for i, p in enumerate(files):
    stat = p.stat()
    identity = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
    digest = inode_cache.get(identity)
    old = prior.get(str(p.relative_to(ROOT)))
    if old and (old['bytes'], old['mtime_ns']) == (stat.st_size, stat.st_mtime_ns):
        digest = old['sha256']
    if digest is None:
        digest = sha(p)
        inode_cache[identity] = digest
    rows.append({'path': str(p.relative_to(ROOT)), 'bytes': stat.st_size,
                 'sha256': digest, 'mode': stat.st_mode & 0o777,
                 'mtime_ns': stat.st_mtime_ns})
    if i % 10000 == 0:
        print('hashed', i, '/', len(files), flush=True)
with gzip.open(META/'files.jsonl.gz', 'wt') as f:
    for row in rows:
        f.write(json.dumps(row, sort_keys=True) + '\n')
(META/'external-links.json').write_text(json.dumps(symlinks, indent=2)+'\n')
(META/'excluded-generated-paths.json').write_text(json.dumps(excluded, indent=2)+'\n')
print('inventory', len(rows), sum(x['bytes'] for x in rows), flush=True)
writer = SplitWriter()
seen = {}
unique_bytes = 0
with gzip.GzipFile(fileobj=writer, mode='wb', compresslevel=3, mtime=0) as zipped:
    with tarfile.open(fileobj=zipped, mode='w|', format=tarfile.PAX_FORMAT) as tar:
        for i, row in enumerate(rows):
            p = ROOT / row['path']
            st = p.stat()
            if (st.st_size, st.st_mtime_ns) != (row['bytes'], row['mtime_ns']):
                raise RuntimeError(f'Input changed: {p}')
            info = tarfile.TarInfo(row['path'])
            info.mode = row['mode']
            info.mtime = st.st_mtime
            info.size = row['bytes']
            key = (row['sha256'], row['mode'])
            if key in seen:
                info.type = tarfile.LNKTYPE
                info.linkname = seen[key]
                info.size = 0
                tar.addfile(info)
            else:
                with p.open('rb') as f:
                    tar.addfile(info, f)
                seen[key] = row['path']
                unique_bytes += row['bytes']
            if i % 10000 == 0:
                print('archived', i, '/', len(rows), 'compressed', writer.position, flush=True)
writer.close()
parts = [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in writer.files]
result = {'schema_version': 1, 'snapshot_date': '2026-09-16',
          'source_commit_before_sync': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
          'roots': ROOTS, 'files': len(rows), 'logical_bytes': sum(x['bytes'] for x in rows),
          'unique_content_mode_pairs': len(seen), 'unique_bytes': unique_bytes,
          'compressed_bytes': sum(x['bytes'] for x in parts), 'parts': parts,
          'catalog_sha256': sha(META/'files.jsonl.gz'), 'external_links': len(symlinks),
          'release_tag': 'process-evidence-20260916',
          'release_url': 'https://github.com/jakekinchen/microduck-rl-genesis/releases/tag/process-evidence-20260916',
          'scope': 'Research/development evidence snapshot; no policy or physical admission.'}
(META/'archive.json').write_text(json.dumps(result, indent=2)+'\n')
(OUT/'SHA256SUMS').write_text(''.join(f"{p['sha256']}  {p['name']}\n" for p in parts))
print(json.dumps(result, indent=2), flush=True)
