create table if not exists public.subscription_audit_logs (
  id bigint generated always as identity primary key,
  actor_user_id uuid not null references auth.users(id) on delete restrict,
  actor_email text not null,
  target_user_id uuid not null references auth.users(id) on delete restrict,
  target_email text not null,
  action text not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.subscription_audit_logs enable row level security;
revoke all on public.subscription_audit_logs from anon, authenticated;
grant all on public.subscription_audit_logs to service_role;
