from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


def _load_env() -> None:
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")


def _get_required_env(name: str, fallback: str | None = None) -> str:
    value = os.getenv(name) or (os.getenv(fallback) if fallback else None)
    if not value or value.startswith("<"):
        if fallback:
            raise SystemExit(f"Missing required env var: {name} (or fallback {fallback}).")
        raise SystemExit(f"Missing required env var: {name}.")
    return value


def _acquire_botframework_token(client_id: str, client_secret: str, tenant_id: str) -> str:
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://api.botframework.com/.default",
    }
    response = requests.post(token_url, data=data, timeout=30)
    if response.status_code != 200:
        raise SystemExit(
            "Failed to acquire AAD token. " f"status={response.status_code}, body={response.text}"
        )

    payload = response.json()
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise SystemExit("Token response did not include access_token.")

    return access_token


def _build_activity(text: str, bot_app_id: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    conversation_id = f"smoke-{uuid.uuid4()}"
    activity_id = str(uuid.uuid4())

    return {
        "id": activity_id,
        "type": "message",
        "timestamp": now,
        "serviceUrl": "https://smba.trafficmanager.net/amer/",
        "channelId": "msteams",
        "from": {"id": "smoke-user", "name": "smoke-user"},
        "recipient": {"id": bot_app_id, "name": "bot"},
        "conversation": {"id": conversation_id, "isGroup": False},
        "text": text,
        "locale": "en-US",
        "deliveryMode": "expectReplies",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Authenticated smoke test for /api/messages end-to-end flow"
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/api/messages",
        help="Messages endpoint URL",
    )
    parser.add_argument(
        "--text",
        default="Smoke test: reply with one short sentence.",
        help="Message text to send",
    )
    args = parser.parse_args()

    _load_env()

    client_id = _get_required_env(
        "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID", "MICROSOFT_APP_ID"
    )
    client_secret = _get_required_env(
        "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET",
        "MICROSOFT_APP_PASSWORD",
    )
    tenant_id = _get_required_env(
        "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID",
        "MICROSOFT_APP_TENANT_ID",
    )

    token = _acquire_botframework_token(client_id, client_secret, tenant_id)
    activity = _build_activity(args.text, client_id)

    response = requests.post(
        args.url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=activity,
        timeout=90,
    )

    print(f"status={response.status_code}")
    body_text = response.text.strip()
    if body_text:
        print(body_text)

    if response.status_code >= 400:
        raise SystemExit("Smoke test failed: HTTP error from /api/messages.")

    try:
        body = response.json() if body_text else {}
    except json.JSONDecodeError:
        body = {}

    if isinstance(body, dict) and isinstance(body.get("activities"), list):
        bot_messages = [
            item.get("text", "")
            for item in body["activities"]
            if isinstance(item, dict) and item.get("type") == "message"
        ]
        if bot_messages:
            print("bot_reply=" + bot_messages[0])
            return

    print(
        "Smoke call succeeded, but no inline activities were returned. "
        "This can happen depending on channel/protocol behavior."
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
