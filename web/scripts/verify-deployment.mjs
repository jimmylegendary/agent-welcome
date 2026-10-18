import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';

const target = process.argv[2];
assert(target, 'Usage: node scripts/verify-deployment.mjs https://your-deployment');
const base = new URL(target);
assert(['https:', 'http:'].includes(base.protocol), 'HTTP(S) deployment URL required');
const publicDir = new URL('../public/', import.meta.url);
const manifest = JSON.parse(await readFile(new URL('guides/manifest.json', publicDir), 'utf8'));
const downloads = (await readdir(new URL('downloads/', publicDir))).filter((name) => !name.startsWith('.'));
const checks = [
  ...['/', '/catalog', '/models', '/compatibility', '/browser-tools', ...manifest.entries.map((entry) => `/guides/${entry.id}`)]
    .map((path) => ({ path, kind: 'page' })),
  ...manifest.entries.map((entry) => ({ path: `/guides/${entry.id}.webp`, kind: 'image' })),
  ...downloads.map((name) => ({ path: `/downloads/${name}`, kind: name.endsWith('.zip') ? 'zip' : name.endsWith('.sql') ? 'sql' : 'file' })),
];
const failures = [];
let passed = 0;
for (let offset = 0; offset < checks.length; offset += 4) {
  await Promise.all(checks.slice(offset, offset + 4).map(async ({ path, kind }) => {
    try {
      const response = await fetch(new URL(path, base), { signal: AbortSignal.timeout(30_000) });
      assert.equal(response.status, 200, `HTTP ${response.status}`);
      const bytes = Buffer.from(await response.arrayBuffer());
      assert(bytes.length > 40, 'Unexpectedly empty response');
      if (kind === 'page') {
        assert(response.headers.get('content-type')?.includes('text/html'), 'Missing HTML content type');
        assert(bytes.toString().includes('lang="ko"'), 'Korean page language missing');
        assert.equal(new URL(response.url).origin, base.origin, 'Unexpected cross-origin redirect');
      } else if (kind === 'image') {
        assert.equal(bytes.toString('ascii', 0, 4), 'RIFF', 'Not a real WebP image');
        assert.equal(bytes.toString('ascii', 8, 12), 'WEBP', 'Not a real WebP image');
      } else if (kind === 'zip') {
        assert.equal(bytes.readUInt32LE(0), 0x04034b50, 'Not a real ZIP download');
      } else {
        assert(!bytes.toString().includes('<!DOCTYPE html>'), 'Download returned HTML');
        if (kind === 'sql') assert(bytes.toString().toLowerCase().includes('function'), 'SQL function download missing');
      }
      passed += 1;
    } catch (error) {
      failures.push({ path, error: error.message });
    }
  }));
}
const notFound = await fetch(new URL('/guides/not-a-real-service', base));
if (notFound.status === 404) passed += 1;
else failures.push({ path: '/guides/not-a-real-service', error: `Expected 404; received ${notFound.status}` });
console.log(JSON.stringify({ target: base.origin, passed, failed: failures.length, failures }, null, 2));
if (failures.length) process.exitCode = 1;
