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
