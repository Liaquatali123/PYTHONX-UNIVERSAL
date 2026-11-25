import os
import uuid
import json
import base64
import zlib
import zipfile
import io
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from pythonx.encryption import MAGIC, detect_protection, encrypt_file, decrypt_file

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
BUCKET = "pythonx-files"
MAX_BYTES = 50 * 1024 * 1024
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"

app = FastAPI(title="PYTHONX UNIVERSAL", version="1.0.0")


def configured():
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(503, "Supabase is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY in Render environment variables.")


async def supabase_request(method: str, path: str, token: str, **kwargs):
    configured()
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {token}",
        **kwargs.pop("headers", {}),
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.request(method, f"{SUPABASE_URL}{path}", headers=headers, **kwargs)
    if response.status_code >= 400:
        try:
            detail = response.json().get("msg") or response.json().get("message") or response.text
        except Exception:
            detail = response.text
        raise HTTPException(response.status_code, str(detail)[:400])
    return response


async def current_user(request: Request):
    configured()
    token = request.cookies.get("px_access")
    if not token:
        raise HTTPException(401, "Please sign in.")
    try:
        response = await supabase_request("GET", "/auth/v1/user", token)
        return response.json(), token
    except HTTPException:
        raise HTTPException(401, "Session expired. Please sign in again.")


def cookie_options():
    return {"httponly": True, "secure": COOKIE_SECURE, "samesite": "lax", "path": "/"}


def set_session_cookies(response, data):
    opts = cookie_options()
    if data.get("access_token"):
        response.set_cookie("px_access", data["access_token"], max_age=int(data.get("expires_in", 3600)), **opts)
    if data.get("refresh_token"):
        response.set_cookie("px_refresh", data["refresh_token"], max_age=60 * 60 * 24 * 30, **opts)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return {"service": "PYTHONX UNIVERSAL API", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health():
    return {"ok": True, "service": "pythonx-universal", "supabase_configured": bool(SUPABASE_URL and SUPABASE_ANON_KEY)}


@app.post("/auth/signup")
async def signup(payload: dict):
    configured()
    email, password = payload.get("email", "").strip(), payload.get("password", "")
    if not email or len(password) < 8:
        raise HTTPException(400, "Email and a password of at least 8 characters are required.")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{SUPABASE_URL}/auth/v1/signup", headers={"apikey": SUPABASE_ANON_KEY}, json={"email": email, "password": password})
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.json().get("msg", r.text)[:300])
    data = r.json()
    response = JSONResponse({"message": "Account created. Check your email if confirmation is enabled.", "session": bool(data.get("access_token"))})
    if data.get("access_token"):
        set_session_cookies(response, data)
    return response


@app.post("/auth/login")
async def login(payload: dict):
    configured()
    email, password = payload.get("email", "").strip(), payload.get("password", "")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", headers={"apikey": SUPABASE_ANON_KEY}, json={"email": email, "password": password})
    if r.status_code >= 400:
        raise HTTPException(401, "Incorrect email/password or email not confirmed.")
    data = r.json()
    response = JSONResponse({"message": "Signed in."})
    set_session_cookies(response, data)
    return response


@app.post("/auth/logout")
async def logout():
    response = JSONResponse({"message": "Signed out."})
    response.delete_cookie("px_access", path="/")
    response.delete_cookie("px_refresh", path="/")
    return response


@app.get("/api/me")
async def me(request: Request):
    user, _ = await current_user(request)
    return {"id": user["id"], "email": user.get("email")}


def inspect_bytes(data: bytes, filename: str):
    result = {"filename": filename, "size_bytes": len(data), "size_human": f"{len(data) / 1024:.1f} KB",
              "encrypted": False, "format": "Unknown / not identified", "decryptable_by_pythonx": False,
              "checks": [], "warnings": []}
    if data.startswith(MAGIC):
        result.update({"encrypted": True, "format": "PYTHONX AES-256-GCM", "decryptable_by_pythonx": True})
        result["checks"].append("PYTHONX authenticated encryption signature found.")
    else:
        with io.BytesIO(data) as stream:
            head = stream.read(1024 * 1024)
        if head.startswith(b"Salted__"):
            result.update(encrypted=True, format="OpenSSL salted encryption container")
        elif head.startswith(b"-----BEGIN PGP MESSAGE-----"):
            result.update(encrypted=True, format="PGP armored message")
        elif head.startswith(b"7z\xbc\xaf\x27\x1c"):
            result.update(format="7-Zip archive (may be encrypted)")
        elif head.startswith(b"Rar!\x1a\x07\x01\x00"):
            result.update(format="RAR5 archive (may be encrypted)")
        elif head.startswith(b"%PDF") and b"/Encrypt" in data[:1024 * 1024]:
            result.update(encrypted=True, format="PDF declares encryption")
        elif zipfile.is_zipfile(io.BytesIO(data)):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    result["format"] = "ZIP archive"
                    result["checks"].append(f"Archive contains {len(zf.infolist())} entries.")
                    if any(info.flag_bits & 1 for info in zf.infolist()):
                        result.update(encrypted=True, format="Password-protected ZIP archive")
            except Exception:
                result["warnings"].append("ZIP directory could not be fully inspected.")
        else:
            result["checks"].append("No known encryption/container signature matched.")
    suffix = Path(filename).suffix.lower()
    if suffix == ".py":
        try:
            compile(data.decode("utf-8"), filename, "exec")
            result["checks"].append("Python syntax check passed; code was not executed.")
        except UnicodeDecodeError:
            result["warnings"].append("Python file is not valid UTF-8.")
        except SyntaxError as exc:
            result["warnings"].append(f"Python syntax issue at line {exc.lineno}: {exc.msg}")
    if not result["decryptable_by_pythonx"] and result["encrypted"]:
        result["warnings"].append("This format cannot be decrypted by PYTHONX without its original legitimate password/key and compatible software.")
    result["warnings"].append("Signature detection is indicative, not proof. Uploaded files are never executed.")
    return result


async def storage_upload(token: str, path: str, data: bytes, content_type: str):
    return await supabase_request("POST", f"/storage/v1/object/{BUCKET}/{path}", token,
        content=data, headers={"Content-Type": content_type, "x-upsert": "false"})


async def create_job(token: str, user_id: str, name: str, input_path: str, operation: str, report: dict):
    payload = {"user_id": user_id, "original_name": name[:255], "input_path": input_path,
               "operation": operation, "status": "completed", "report": report}
    r = await supabase_request("POST", "/rest/v1/jobs", token, json=payload,
        headers={"Content-Type": "application/json", "Prefer": "return=representation"})
    return r.json()[0]


@app.post("/api/process")
async def process_file(request: Request, file: UploadFile = File(...), operation: str = Form("scan"), password: Optional[str] = Form(None)):
    user, token = await current_user(request)
    if operation not in {"scan", "encrypt", "decrypt"}:
        raise HTTPException(400, "Unsupported operation.")
    if operation in {"encrypt", "decrypt"} and (not password or len(password) < 8):
        raise HTTPException(400, "Enter a password with at least 8 characters.")
    original_name = Path(file.filename or "upload.bin").name[:255]
    data = await file.read(MAX_BYTES + 1)
    if not data:
        raise HTTPException(400, "The selected file is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Maximum upload size is 50 MB.")
    if operation == "decrypt" and not data.startswith(MAGIC):
        raise HTTPException(400, "Only PYTHONX AES-256-GCM files can be decrypted here. Other formats need their original software and key.")
    job_id = str(uuid.uuid4())
    prefix = f"{user['id']}/{job_id}"
    input_path = f"{prefix}/original-{original_name}"
    content_type = file.content_type or "application/octet-stream"
    await storage_upload(token, input_path, data, content_type)
    report = inspect_bytes(data, original_name)
    output_path = None
    output_name = None
    if operation in {"encrypt", "decrypt"}:
        import tempfile
        with tempfile.TemporaryDirectory(prefix="pythonx-") as temp:
            src = Path(temp) / "input.bin"
            dst = Path(temp) / ("protected.pyx" if operation == "encrypt" else f"recovered-{original_name}")
            src.write_bytes(data)
            try:
                if operation == "encrypt":
                    encrypt_file(src, dst, password)
                else:
                    decrypt_file(src, dst, password)
            except (ValueError, RuntimeError) as exc:
                raise HTTPException(400, str(exc))
            output = dst.read_bytes()
            output_name = dst.name
            output_path = f"{prefix}/{output_name}"
            await storage_upload(token, output_path, output, "application/octet-stream")
            report["result"] = {"filename": output_name, "size_bytes": len(output)}
    job = await create_job(token, user["id"], original_name, input_path, operation, report)
    return {"job_id": job_id, "record_id": job["id"], "report": report, "output_available": bool(output_path),
            "output_name": output_name, "output_path": output_path}


@app.get("/api/history")
async def history(request: Request):
    _, token = await current_user(request)
    r = await supabase_request("GET", "/rest/v1/jobs?select=id,original_name,operation,status,report,created_at&order=created_at.desc&limit=50", token)
    return r.json()


@app.get("/api/download")
async def download(request: Request, path: str):
    user, token = await current_user(request)
    if not path.startswith(f"{user['id']}/") or ".." in path.split("/"):
        raise HTTPException(403, "Not allowed.")
    r = await supabase_request("GET", f"/storage/v1/object/{BUCKET}/{path}", token)
    filename = Path(path).name.replace('"', "")
    return StreamingResponse(io.BytesIO(r.content), media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
