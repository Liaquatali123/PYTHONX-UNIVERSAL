drop policy if exists "Deny client access to subscription audit logs" on public.subscription_audit_logs;
create policy "Deny client access to subscription audit logs"
on public.subscription_audit_logs
for all
to anon, authenticated
using (false)
with check (false);
