# PYTHONX UNIVERSAL

PYTHONX UNIVERSAL is split into two deployments:

- **Frontend (Vercel):** static website and dashboard in `frontend/`.
- **Python API (Render):** FastAPI backend at `https://pythonx-universal.onrender.com`.
- **Supabase:** Auth, Postgres job history, and private file storage.
- **GitHub:** source repository and automatic deployment trigger.

The Vercel frontend uses rewrites in `frontend/vercel.json` to proxy `/auth/*`, `/api/*`, and `/health` to the Render API. This keeps browser requests same-origin, so the HttpOnly session cookies work without exposing tokens to JavaScript.

## Deployments

### Vercel frontend
- Repository: `Liaquatali123/PYTHONX-UNIVERSAL`
- Root directory: `frontend`
- Production domain: `https://pythonx-universal-web.vercel.app`
- Static site; no frontend build command required.

### Render Python API
- Repository: `Liaquatali123/PYTHONX-UNIVERSAL`
- Root directory: repository root
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`
- Region: Singapore; free plan may sleep while idle.

Set these Render environment variables:
- `SUPABASE_URL=https://boaugmzcyyvewvrrxzgr.supabase.co`
- `SUPABASE_ANON_KEY=<Supabase publishable key>`
- `COOKIE_SECURE=true`

Do not place a Supabase secret/service-role key in frontend code. The backend uses the user's Supabase access token and database/storage RLS policies.

## Supabase setup

- `public.jobs` has row-level security restricting each record to its owner.
- Private Storage bucket: `pythonx-files`, 50 MB object limit.
- Storage policies restrict access to the authenticated user's UUID folder.
- Email confirmation behavior follows the Supabase Auth project settings.

## Features and limits

- Email/password sign-up and sign-in.
- Private file inspection and job history.
- Signature inspection for PYTHONX, OpenSSL, PGP, PDF encryption markers, ZIP, 7z/RAR containers.
- Protect files with PYTHONX AES-256-GCM.
- Decrypt PYTHONX files only with the correct password.
- Python syntax checks without executing uploaded code.
- 50 MB upload limit.
- No password cracking, AES breaking, DRM bypass, or execution of uploaded files.
- Detection is indicative, not proof; other formats require their original password/key and compatible software.
- Render's free service may sleep and has limited CPU/memory. Heavy concurrent processing may require a paid plan.

## Local API development

```bash
python -m venv .venv
pip install -r requirements.txt
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co SUPABASE_ANON_KEY=YOUR_PUBLISHABLE_KEY uvicorn app:app --reload
```

MIT License; see [LICENSE](LICENSE).


## Subscription plans and manual upgrades

The dashboard shows these server-enforced daily processing quotas:

| Plan | Jobs per UTC day | Max upload |
|---|---:|---:|
| Free | 5 | 50 MB |
| Pro | 50 | 50 MB |
| Plus | 200 | 50 MB |
| Max | 500 | 50 MB |

Paid plans increase the daily quota. Prices are intentionally not displayed until the owner sets them. All plans have a 50 MB maximum upload.

Upgrade contacts:
- Telegram: https://t.me/LiaqatAliPro
- Email: liaqatalicontact001@gmail.com
- WhatsApp: https://wa.me/923451160017
- Developer: Liaquat Ali

After confirming payment, activate a plan from the Supabase SQL editor (replace the customer email and plan):

```sql
insert into public.user_subscriptions (user_id, plan, status, expires_at)
select id, 'pro', 'active', now() + interval '30 days'
from auth.users where email = 'CUSTOMER_EMAIL'
on conflict (user_id) do update
set plan = excluded.plan, status = excluded.status,
    expires_at = excluded.expires_at, updated_at = now();
```

Users can read only their own subscription. Authenticated users cannot edit their plan; only trusted project administrators can activate upgrades.

## API protection notes

- Processing routes require a valid Supabase session cookie (HttpOnly, Secure, SameSite=Lax).
- Plan and daily quota checks happen in the Python API, not in frontend JavaScript.
- Job history and private file storage remain protected by Supabase RLS and user-folder policies.
- API URLs and requests cannot be made impossible to inspect. The protection is server-side authorization, quotas, validation, and keeping privileged secrets off the client—not hiding endpoint URLs.


## Admin roles and subscription management

The API enforces roles server-side. Only these exact email addresses are allowed to use the admin API:

- `rdxkinglucky@gmail.com`
- `liaquatalisoomroali@gmail.com`

Set `ADMIN_EMAILS` on the Render API service to the comma-separated allowlist. This is already configured for the production service. All other signed-in accounts receive the `user` role and are denied admin endpoints.

For plan management, set `SUPABASE_SERVICE_ROLE_KEY` on the Render API service to the Supabase project **secret key** (preferred, starts with `sb_secret_`) or legacy service-role key. Never add this key to Vercel, frontend code, GitHub, or a chat message. The backend first validates the caller's Supabase Auth session and checks the email allowlist; only then does it use the server-side key for Auth user lookup and subscription writes.

The website's Admin Control Center is visible only to the two allowlisted admins. It supports account lookup and plan/status changes. Subscription changes are recorded in `public.subscription_audit_logs`; the table denies all client-role access. Normal users can only read their own subscription, and cannot create or change plan records.

Apply the migrations in `supabase/migrations` to the linked Supabase project. Admin plan management remains unavailable until `SUPABASE_SERVICE_ROLE_KEY` is configured in Render.
