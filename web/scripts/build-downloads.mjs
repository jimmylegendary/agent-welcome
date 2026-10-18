import { execFileSync } from 'node:child_process';
import { access, mkdir, readdir, stat } from 'node:fs/promises';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const webDir = resolve(scriptDir, '..');
const resourcesDir = join(webDir, 'resources');
const downloadsDir = join(webDir, 'public', 'downloads');
const bundles = [
  { source: 'codex-openrouter', output: 'codex-openrouter-starter.zip' },
  { source: 'nextjs-zustand-starter', output: 'nextjs-zustand-starter.zip' },
  { source: 'flutter-riverpod-mvvm-starter', output: 'flutter-riverpod-mvvm-starter.zip' },
  { source: 'jimmy-skills', output: 'jimmy-skills-starter.zip' },
  { source: 'playwright-public-crawler', output: 'playwright-public-crawler.zip' },
];

const zipPython = String.raw`
import os
import stat
import sys
import zipfile
from pathlib import Path

source = Path(sys.argv[1]).resolve()
destination = Path(sys.argv[2]).resolve()
prefix = source.name
excluded_names = {'.DS_Store', '.git', 'node_modules', '.dart_tool', 'output'}
files = sorted(
    item for item in source.rglob('*')
    if item.is_file() and not item.is_symlink()
    and not any(part in excluded_names for part in item.relative_to(source).parts)
)
for item in files:
    name = item.name
    if name == '.env' or (name.startswith('.env.') and name != '.env.example'):
        raise SystemExit(f'Refusing to package secret-like file: {item.relative_to(source)}')
if not files:
    raise SystemExit(f'No source files found: {source}')

destination.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(destination, 'w') as archive:
    for item in files:
        member = Path(prefix) / item.relative_to(source)
        mode = stat.S_IFREG | (0o755 if os.access(item, os.X_OK) else 0o644)
        info = zipfile.ZipInfo(member.as_posix(), date_time=(2026, 10, 18, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = mode << 16
        archive.writestr(info, item.read_bytes())
print(f'Wrote {destination.name}: {len(files)} files')
`;

await access(resourcesDir);
await mkdir(downloadsDir, { recursive: true });

for (const bundle of bundles) {
  const source = join(resourcesDir, bundle.source);
  const sourceStat = await stat(source);
  if (!sourceStat.isDirectory()) throw new Error(`Bundle source is not a directory: ${source}`);

  const topLevel = await readdir(source);
  if (topLevel.length === 0) throw new Error(`Bundle source is empty: ${source}`);

  const destination = join(downloadsDir, bundle.output);
  execFileSync('python3', ['-c', zipPython, source, destination], { stdio: 'inherit' });
  console.log(`${relative(webDir, destination).split(sep).join('/')}`);
}
