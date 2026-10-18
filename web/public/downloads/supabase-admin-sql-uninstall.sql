-- Remove only the Simple Mode administrative SQL RPC.
-- This leaves tables, data, grants, and other project objects untouched.

begin;

drop function if exists public.simple_mode_admin_sql(text);

commit;
