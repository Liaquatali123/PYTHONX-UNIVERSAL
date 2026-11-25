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
