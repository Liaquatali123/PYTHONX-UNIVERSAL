# PYTHONX UNIVERSAL

PYTHONX UNIVERSAL is a server-hosted file inspection and protection workspace. The website runs on Render; user accounts, job history and private uploaded files use Supabase. File operations run on the server, not on the visitor's device.

## Features

- Supabase email/password sign-up and sign-in.
- Private per-user file storage and processing history.
- File signature inspection for PYTHONX, OpenSSL, PGP, PDF encryption markers, ZIP and 7z/RAR containers.
- Protect files with PYTHONX AES-256-GCM encryption.
- Decrypt only PYTHONX files when the correct original password is supplied.
- Python syntax checks without executing uploaded code.
- 50 MB upload limit; no password cracking, DRM bypass or execution of uploaded files.

## Deployment

The repository includes `render.yaml`. In Render, create a Blueprint from this repository or create a Python web service with:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`
- Region: Singapore
- Plan: Free (subject to Render free-tier sleep and resource limits)

Set these environment variables in Render:

- `SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co`
- `SUPABASE_ANON_KEY=YOUR_SUPABASE_PUBLISHABLE_KEY`
- `COOKIE_SECURE=true`

Never put a Supabase secret/service-role key in the browser. This application uses the user's Supabase access token and database/storage RLS policies.

## Supabase setup

The migration creates:
- `public.jobs` with row-level security restricting records to their owner.
- Private Storage bucket `pythonx-files` (50 MB limit).
- Storage policies limiting access to the authenticated user's UUID folder.

Email confirmation behavior follows the Supabase Auth project settings. Users may need to confirm their email before signing in.

## Local development

```bash
python -m venv .venv
# activate the environment, then:
pip install -r requirements.txt
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co SUPABASE_ANON_KEY=YOUR_PUBLISHABLE_KEY uvicorn app:app --reload
```

## Security and limitations

- Uploaded content is processed in server memory or temporary files and is never executed.
- Files are stored in a private bucket under `<user_id>/<job_id>/`.
- The app only decrypts its own authenticated PYTHONX AES-256-GCM format. It cannot recover unknown passwords or decrypt third-party formats without their legitimate key/software.
- Detection is signature-based and indicative, not proof.
- Render's free service may sleep when idle and has limited memory/CPU. Large or concurrent recovery jobs may require a paid worker/server.
- Configure retention and deletion policies before using this for sensitive production workloads.

MIT License; see [LICENSE](LICENSE).
