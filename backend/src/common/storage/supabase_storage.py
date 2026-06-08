"""
Supabase Storage helpers for backend-mediated signed uploads and object checks.

Uses the service role key server-side only. Browser clients never receive the
service role key; they receive short-lived signed upload URLs from owner APIs.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)


class SupabaseStorageError(RuntimeError):
    pass


@dataclass(frozen=True)
class SignedUploadResult:
    signed_upload_url: str
    path: str
    token: str | None


def _project_base_url() -> str:
    return str(settings.SUPABASE_URL).rstrip("/")


def _service_role_key() -> str:
    key = str(getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "") or "").strip()
    if not key:
        raise SupabaseStorageError(
            "SUPABASE_SERVICE_ROLE_KEY is not configured for storage operations."
        )
    return key


def _storage_request(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict:
    key = _service_role_key()
    url = f"{_project_base_url()}{path}"
    data = None
    headers = {
        "Authorization": f"Bearer {key}",
        "apikey": key,
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            if not raw.strip():
                return {}
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise SupabaseStorageError("Unexpected storage API response shape.")
            return parsed
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        logger.warning(
            "Supabase storage request failed: %s %s — %s",
            method,
            path,
            detail,
        )
        raise SupabaseStorageError(
            f"Storage request failed ({exc.code}): {detail or exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SupabaseStorageError(f"Storage request failed: {exc}") from exc


def create_signed_upload_url(
    bucket: str,
    object_path: str,
    *,
    expires_in_seconds: int = 600,
) -> SignedUploadResult:
    """
    Issue a signed upload URL via Supabase Storage REST API.

    POST /storage/v1/object/upload/sign/{bucket}/{path}
    """
    encoded_path = "/".join(
        urllib.parse.quote(segment, safe="") for segment in object_path.split("/")
    )
    api_path = f"/storage/v1/object/upload/sign/{bucket.strip('/')}/{encoded_path}"
    payload = _storage_request("POST", api_path, body={"expiresIn": expires_in_seconds})

    signed_url = (
        payload.get("signedUrl")
        or payload.get("signedURL")
        or payload.get("signed_upload_url")
        or payload.get("url")
    )
    if not signed_url or not isinstance(signed_url, str):
        raise SupabaseStorageError("Storage API did not return a signed upload URL.")

    path = payload.get("path")
    if not isinstance(path, str):
        path = object_path.lstrip("/")

    token = payload.get("token")
    if token is not None and not isinstance(token, str):
        token = None

    return SignedUploadResult(
        signed_upload_url=signed_url,
        path=path,
        token=token,
    )


def storage_object_exists(bucket: str, object_path: str) -> bool:
    """
    HEAD check whether an object exists in Storage.

    Returns False when service role is unavailable (e.g. unit tests without key).
    """
    try:
        key = _service_role_key()
    except SupabaseStorageError:
        return False

    encoded_path = "/".join(
        urllib.parse.quote(segment, safe="") for segment in object_path.lstrip("/").split("/")
    )
    url = (
        f"{_project_base_url()}/storage/v1/object/{bucket.strip('/')}/{encoded_path}"
    )
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"Authorization": f"Bearer {key}", "apikey": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        logger.warning("Storage HEAD failed for %s/%s: %s", bucket, object_path, exc)
        return False
    except urllib.error.URLError:
        return False
