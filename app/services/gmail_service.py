import base64
import json
import logging
from datetime import UTC, datetime
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.credentials import Credentials

from app.core.config import settings


log = logging.getLogger(__name__)


def is_enabled() -> bool:
    return bool(settings.gmail_client_secret_json and settings.gmail_token_json)


def build_gmail_client() -> Any:
    if not is_enabled():
        raise RuntimeError("Gmail integration is not configured. Set GMAIL_CLIENT_SECRET_JSON and GMAIL_TOKEN_JSON.")

    token_info = json.loads(settings.gmail_token_json or "{}")
    if "client_id" not in token_info or "client_secret" not in token_info:
        token_info.update(_extract_client_id_secret())
    creds = Credentials.from_authorized_user_info(token_info, scopes=_scopes())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _scopes() -> list[str]:
    return [s.strip() for s in (settings.gmail_scopes or "").split(",") if s.strip()]


def _extract_client_id_secret() -> dict[str, str]:
    raw = settings.gmail_client_secret_json
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    candidate = parsed.get("installed") or parsed.get("web") or {}
    client_id = candidate.get("client_id")
    client_secret = candidate.get("client_secret")
    out: dict[str, str] = {}
    if client_id and client_secret:
        out["client_id"] = client_id
        out["client_secret"] = client_secret
    return out

def list_recent_messages(max_results: int = 25) -> list[dict[str, Any]]:
    svc = build_gmail_client()
    try:
        resp = svc.users().messages().list(userId="me", maxResults=max_results).execute()
        return resp.get("messages", []) or []
    except HttpError as e:
        log.exception("Gmail API error listing messages: %s", e)
        return []


def get_message(message_id: str) -> dict[str, Any] | None:
    svc = build_gmail_client()
    try:
        return svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    except HttpError as e:
        log.exception("Gmail API error fetching message %s: %s", message_id, e)
        return None


def extract_email_fields(msg: dict[str, Any]) -> dict[str, Any]:
    payload = msg.get("payload", {}) or {}
    headers = {h.get("name", "").lower(): h.get("value") for h in (payload.get("headers") or [])}
    subject = headers.get("subject")
    sender = headers.get("from")

    internal_date_ms = msg.get("internalDate")
    received_at = None
    if internal_date_ms:
        try:
            received_at = datetime.fromtimestamp(int(internal_date_ms) / 1000, tz=UTC)
        except ValueError:
            received_at = None

    body = _extract_body(payload)
    label_ids = msg.get("labelIds") or []
    is_unread = "UNREAD" in label_ids

    return {
        "message_id": msg.get("id"),
        "thread_id": msg.get("threadId"),
        "subject": subject,
        "sender": sender,
        "received_at": received_at,
        "snippet": msg.get("snippet"),
        "body": body,
        "labels": ",".join(label_ids),
        "is_unread": is_unread,
    }


def _extract_body(payload: dict[str, Any]) -> str | None:
    def decode(data: str) -> str:
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")

    if payload.get("body", {}).get("data"):
        return decode(payload["body"]["data"])

    for part in payload.get("parts") or []:
        mime_type = part.get("mimeType")
        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            return decode(part["body"]["data"])

    for part in payload.get("parts") or []:
        mime_type = part.get("mimeType")
        if mime_type == "text/html" and part.get("body", {}).get("data"):
            return decode(part["body"]["data"])

    return None
