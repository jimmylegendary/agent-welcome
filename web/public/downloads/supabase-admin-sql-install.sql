-- Simple Mode: install a server-only administrative SQL RPC.
--
-- Run this entire file once in the Supabase Dashboard SQL Editor while signed in
-- as the project database owner. It creates a SECURITY DEFINER function owned
-- by postgres. Any p_sql passed to the function runs with that owner's database
-- privileges. A caller able to use this endpoint can alter or delete project
-- data and database objects. Only call it from a trusted, authorization-checked
-- backend. Never put a Supabase secret/service_role key or this RPC in a browser,
-- shipped app, public endpoint, or source control.
--
-- Function privileges are restricted to service_role. The API role check is an
-- additional guard for signed Supabase Data API requests. The pinned empty
-- search_path and schema-qualified objects follow Supabase's SECURITY DEFINER
-- guidance: https://supabase.com/docs/guides/database/functions
--
-- DROP + CREATE intentionally clears any old ACL, including grants to custom
-- roles. It runs in this transaction and has no CASCADE: if another database
-- object depends on this function, installation fails and rolls back safely.

begin;

drop function if exists public.simple_mode_admin_sql(text);

create function public.simple_mode_admin_sql(p_sql text)
returns jsonb
language plpgsql
volatile
security definer
set search_path = ''
as $function$
declare
  v_rows_affected bigint;
begin
  if auth.role() is distinct from 'service_role' then
    raise exception 'simple_mode_admin_sql requires a service_role API request'
      using errcode = '42501';
  end if;

  if p_sql is null or pg_catalog.btrim(p_sql) = '' then
    raise exception 'p_sql must contain one SQL statement'
      using errcode = '22023';
  end if;

  -- PostgreSQL executes the dynamic command in this function's transaction.
  -- Any error aborts the RPC statement and rolls back its database changes.
  -- Send one SQL command per RPC call; result rows from SELECT are discarded.
  execute p_sql;
  get diagnostics v_rows_affected = row_count;

  return pg_catalog.jsonb_build_object(
    'ok', true,
    'rows_affected', v_rows_affected
  );
end;
$function$;

-- The SQL Editor normally creates this function as postgres. Make the required
-- SECURITY DEFINER owner explicit; Supabase documents this role as privileged.
alter function public.simple_mode_admin_sql(text) owner to postgres;

revoke all privileges on function public.simple_mode_admin_sql(text)
  from public, anon, authenticated, service_role;
grant execute on function public.simple_mode_admin_sql(text) to service_role;

comment on function public.simple_mode_admin_sql(text) is
  'Simple Mode trusted-backend SQL RPC. Executes one caller-supplied statement with postgres owner privileges; never expose to browsers or untrusted callers.';

commit;
