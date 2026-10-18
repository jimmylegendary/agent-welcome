#!/usr/bin/env node

/**
 * Run the Supabase SQL lifecycle against an in-memory PostgreSQL fixture.
 * No Supabase account, credentials, network, or persistent database is used.
 *
 * Install the test-only dependency outside the repository, then run:
 *   npm install --prefix /tmp/simple-mode-supabase-test-deps --no-save --ignore-scripts --no-audit --no-fund @electric-sql/pglite
 *   PGLITE_MODULE_DIR=/tmp/simple-mode-supabase-test-deps/node_modules node scripts/test-supabase.mjs
 */

import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(scriptDir, '..');
const downloadsDir = path.join(webRoot, 'public', 'downloads');
const moduleDir = process.env.PGLITE_MODULE_DIR;

if (!moduleDir) {
  throw new Error('Set PGLITE_MODULE_DIR to the isolated node_modules directory.');
}

const requireFromFixture = createRequire(path.join(moduleDir, 'package.json'));
const pgliteEntry = requireFromFixture.resolve('@electric-sql/pglite');
const { PGlite } = await import(pathToFileURL(pgliteEntry).href);
const database = new PGlite();

const installSql = await fs.readFile(path.join(downloadsDir, 'supabase-admin-sql-install.sql'), 'utf8');
const checkSql = await fs.readFile(path.join(downloadsDir, 'supabase-admin-sql-check.sql'), 'utf8');
const uninstallSql = await fs.readFile(path.join(downloadsDir, 'supabase-admin-sql-uninstall.sql'), 'utf8');
const passes = [];

function pass(label) {
  passes.push(label);
  console.log(`PASS ${label}`);
}

async function setupSupabaseRolesAndStaleGrant() {
  await database.exec(`
    create role anon;
    create role authenticated;
    create role service_role;
    create role simple_mode_custom;
    create schema auth;
    create function auth.role() returns text
      language sql stable
      as $$ select current_setting('request.jwt.claim.role', true) $$;
    create function public.simple_mode_admin_sql(p_sql text) returns jsonb
      language sql as $$ select '{}'::jsonb $$;
    grant execute on function public.simple_mode_admin_sql(text) to simple_mode_custom;
  `);
}

async function checkRow() {
  const { rows } = await database.query(checkSql);
  assert.equal(rows.length, 1, 'permission check must return exactly one row');
  return rows[0];
}

await setupSupabaseRolesAndStaleGrant();
assert.equal(
  (await database.query(`select has_function_privilege('simple_mode_custom', 'public.simple_mode_admin_sql(text)', 'EXECUTE') as granted`)).rows[0].granted,
  true,
  'fixture must begin with a stale custom-role grant',
);
pass('fixture starts with a pre-existing custom-role EXECUTE grant');

await database.exec(installSql);
let permissions = await checkRow();
assert.equal(permissions.installed, true);
assert.equal(permissions.is_security_definer, true);
assert.equal(permissions.owner_is_postgres, true);
assert.equal(permissions.search_path_is_empty, true);
assert.equal(permissions.service_role_can_execute, true);
assert.equal(permissions.public_execute_revoked, true);
assert.equal(permissions.anon_execute_revoked, true);
assert.equal(permissions.authenticated_execute_revoked, true);
assert.equal(permissions.no_unexpected_execute_grantees, true);
assert.equal(permissions.no_unexpected_effective_execute_roles, true);
assert.equal(permissions.overall_status, 'PASS');
assert.equal(
  (await database.query(`select has_function_privilege('simple_mode_custom', 'public.simple_mode_admin_sql(text)', 'EXECUTE') as granted`)).rows[0].granted,
  false,
  'DROP + CREATE must clear stale custom-role grants',
);
pass('install replaces the old function and removes stale grants to custom roles');
pass('read-only check accepts only postgres owner plus service_role execution');

// Deliberately restore an unexpected direct grant: the check must fail closed.
await database.exec('grant execute on function public.simple_mode_admin_sql(text) to simple_mode_custom;');
permissions = await checkRow();
assert.equal(permissions.no_unexpected_execute_grantees, false);
assert.equal(permissions.overall_status, 'FAIL');
pass('check fails when a custom role receives an unexpected direct grant');

await database.exec('revoke execute on function public.simple_mode_admin_sql(text) from simple_mode_custom; grant service_role to simple_mode_custom;');
permissions = await checkRow();
assert.equal(permissions.no_unexpected_execute_grantees, true);
assert.equal(permissions.no_unexpected_effective_execute_roles, false);
assert.equal(permissions.overall_status, 'FAIL');
await database.exec('revoke service_role from simple_mode_custom;');
pass('check also fails on indirect EXECUTE inherited through service_role membership');

// Reinstall must remove that custom ACL rather than preserve it.
await database.exec(installSql);
permissions = await checkRow();
assert.equal(permissions.no_unexpected_execute_grantees, true);
assert.equal(permissions.overall_status, 'PASS');
pass('reinstall removes the unexpected custom-role grant and restores PASS');

await database.exec("set request.jwt.claim.role = 'service_role';");
const createResult = await database.query(
  `select public.simple_mode_admin_sql($1) as result`,
  ['CREATE TABLE public.fixture_created (id bigint PRIMARY KEY)'],
);
assert.deepEqual(createResult.rows[0].result, { ok: true, rows_affected: 0 });
assert.equal(
  (await database.query("select to_regclass('public.fixture_created') is not null as exists")).rows[0].exists,
  true,
);
pass('service_role request can create a table and receives explicit success evidence');

await assert.rejects(
  database.query('select public.simple_mode_admin_sql($1)', ['   ']),
  (error) => error.code === '22023',
);
pass('empty SQL is rejected with SQLSTATE 22023');

for (const role of ['anon', 'authenticated']) {
  await database.exec(`set request.jwt.claim.role = '${role}';`);
  await assert.rejects(
    database.query('select public.simple_mode_admin_sql($1)', [`CREATE TABLE public.${role}_must_not_exist (id int)`]),
    (error) => error.code === '42501',
  );
  assert.equal(
    (await database.query(`select to_regclass('public.${role}_must_not_exist') is null as absent`)).rows[0].absent,
    true,
  );
  pass(`${role} request is denied before executing SQL`);
}

await database.exec("set request.jwt.claim.role = 'service_role';");
const failingBlock = `DO $rollback$
BEGIN
  CREATE TABLE public.fixture_rollback (id int);
  RAISE EXCEPTION 'intentional fixture failure';
END;
$rollback$;`;
await assert.rejects(
  database.query('select public.simple_mode_admin_sql($1)', [failingBlock]),
  (error) => error.message.includes('intentional fixture failure'),
);
assert.equal(
  (await database.query("select to_regclass('public.fixture_rollback') is null as absent")).rows[0].absent,
  true,
  'the failing RPC statement must roll back its DDL',
);
pass('a SQL error rolls back DDL performed earlier in the same RPC transaction');

await database.exec(uninstallSql);
assert.equal(
  (await database.query("select to_regprocedure('public.simple_mode_admin_sql(text)') is null as absent")).rows[0].absent,
  true,
);
assert.equal(
  (await database.query("select to_regclass('public.fixture_created') is not null as remains")).rows[0].remains,
  true,
);
permissions = await checkRow();
assert.equal(permissions.installed, false);
assert.equal(permissions.overall_status, 'FAIL');
pass('uninstall removes only the function and preserves a table it created');

await database.close();
console.log(`\n${passes.length} Supabase SQL fixture checks passed (in-memory PGlite only).`);
