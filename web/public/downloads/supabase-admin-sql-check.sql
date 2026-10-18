-- Read-only verification for the Simple Mode administrative SQL RPC.
-- Run in the Supabase Dashboard SQL Editor. It does not call the RPC or change
-- project objects. Every boolean should be true; overall_status should be PASS.

with target as (
  select pg_catalog.to_regprocedure(
    'public.simple_mode_admin_sql(text)'
  ) as function_oid
), metadata as (
  select
    p.oid,
    p.proowner,
    p.prosecdef,
    p.proconfig,
    pg_catalog.has_function_privilege('service_role', p.oid, 'EXECUTE')
      as service_role_can_execute,
    pg_catalog.has_function_privilege('anon', p.oid, 'EXECUTE')
      as anon_can_execute,
    pg_catalog.has_function_privilege('authenticated', p.oid, 'EXECUTE')
      as authenticated_can_execute,
    exists (
      select 1
      from pg_catalog.aclexplode(
        coalesce(p.proacl, pg_catalog.acldefault('f', p.proowner))
      ) as acl
      where acl.grantee = 0
        and acl.privilege_type = 'EXECUTE'
    ) as public_can_execute,
    exists (
      select 1
      from pg_catalog.aclexplode(
        coalesce(p.proacl, pg_catalog.acldefault('f', p.proowner))
      ) as acl
      where acl.privilege_type = 'EXECUTE'
        and acl.grantee not in (
          p.proowner,
          (select r.oid from pg_catalog.pg_roles as r where r.rolname = 'service_role')
        )
    ) as unexpected_execute_grantee,
    exists (
      select 1
      from pg_catalog.pg_roles as r
      where r.rolname not in ('postgres', 'service_role')
        and not r.rolsuper
        and pg_catalog.has_function_privilege(r.oid, p.oid, 'EXECUTE')
    ) as unexpected_effective_execute_role,
    exists (
      select 1
      from pg_catalog.unnest(coalesce(p.proconfig, array[]::text[])) as cfg
      where pg_catalog.split_part(cfg, '=', 1) = 'search_path'
        and pg_catalog.translate(pg_catalog.split_part(cfg, '=', 2), '"', '') = ''
    ) as empty_search_path
  from pg_catalog.pg_proc as p
  where p.oid = (select function_oid from target)
)
select
  (target.function_oid is not null) as installed,
  coalesce(metadata.prosecdef, false) as is_security_definer,
  coalesce(metadata.proowner = 'postgres'::pg_catalog.regrole, false)
    as owner_is_postgres,
  coalesce(metadata.empty_search_path, false) as search_path_is_empty,
  coalesce(metadata.service_role_can_execute, false)
    as service_role_can_execute,
  coalesce(not metadata.public_can_execute, false)
    as public_execute_revoked,
  coalesce(not metadata.anon_can_execute, false) as anon_execute_revoked,
  coalesce(not metadata.authenticated_can_execute, false)
    as authenticated_execute_revoked,
  coalesce(not metadata.unexpected_execute_grantee, false)
    as no_unexpected_execute_grantees,
  coalesce(not metadata.unexpected_effective_execute_role, false)
    as no_unexpected_effective_execute_roles,
  case
    when target.function_oid is not null
      and metadata.prosecdef
      and metadata.proowner = 'postgres'::pg_catalog.regrole
      and metadata.empty_search_path
      and metadata.service_role_can_execute
      and not metadata.public_can_execute
      and not metadata.unexpected_execute_grantee
      and not metadata.unexpected_effective_execute_role
      and not metadata.anon_can_execute
      and not metadata.authenticated_can_execute
    then 'PASS'
    else 'FAIL'
  end as overall_status
from target
left join metadata on true;
