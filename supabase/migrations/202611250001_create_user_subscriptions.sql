create table if not exists public.user_subscriptions (
  user_id uuid primary key references auth.users(id) on delete cascade,
  plan text not null default 'free' check (plan in ('free','pro','plus','max')),
  status text not null default 'active' check (status in ('active','expired','suspended')),
  expires_at timestamptz,
  updated_at timestamptz not null default now()
);
alter table public.user_subscriptions enable row level security;
revoke all on public.user_subscriptions from anon, authenticated;
grant select on public.user_subscriptions to authenticated;
drop policy if exists "Users can read their own subscription" on public.user_subscriptions;
create policy "Users can read their own subscription"
on public.user_subscriptions for select to authenticated
using ((select auth.uid()) = user_id);
