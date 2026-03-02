#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
ENV_FILE = PROJECT_ROOT / ".env"

DEFAULT_COLOR_ICON = ROOT / "default-color-icon.png"
DEFAULT_OUTLINE_ICON = ROOT / "default-outline-icon.png"

BUILD_DIR = ROOT / "build"
PACKAGE_DIR = BUILD_DIR / "package"
OUTPUT_ZIP = BUILD_DIR / "teams-app-package.zip"


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def main() -> None:
    env = parse_env(ENV_FILE)

    bot_app_id = env.get("MICROSOFT_APP_ID", "").strip()
    bot_endpoint = env.get("BOT_ENDPOINT", "").strip()
    teams_app_id = env.get("TEAMS_APP_ID", "").strip() or str(uuid.uuid4())

    if not bot_app_id:
        raise ValueError("MICROSOFT_APP_ID is required in .env")
    if not bot_endpoint:
        raise ValueError("BOT_ENDPOINT is required in .env")

    bot_domain = urlparse(bot_endpoint).netloc
    if not bot_domain:
        raise ValueError("Invalid BOT_ENDPOINT")

    manifest = {
        "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.17/MicrosoftTeams.schema.json",
        "manifestVersion": "1.17",
        "version": "1.0.0",
        "id": teams_app_id,
        "name": {
            "short": "Foundry Bot",
            "full": "Foundry Agent Teams Bot",
        },
        "developer": {
            "name": "AI Foundry Demo",
            "websiteUrl": "https://learn.microsoft.com",
            "privacyUrl": "https://learn.microsoft.com/legal/privacy",
            "termsOfUseUrl": "https://learn.microsoft.com/legal/termsofuse",
        },
        "description": {
            "short": "Foundry-powered Teams assistant.",
            "full": "Teams bot backed by Azure Bot Service, ACA FastAPI app, and Azure AI Foundry agent.",
        },
        "icons": {
            "outline": "outline.png",
            "color": "color.png",
        },
        "accentColor": "#6264A7",
        "bots": [
            {
                "botId": bot_app_id,
                "scopes": ["personal", "team", "groupchat"],
                "supportsFiles": False,
                "isNotificationOnly": False,
            }
        ],
        "permissions": ["identity", "messageTeamMembers"],
        "validDomains": [bot_domain, "token.botframework.com"],
    }

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    manifest_path = PACKAGE_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    shutil.copyfile(DEFAULT_COLOR_ICON, PACKAGE_DIR / "color.png")
    shutil.copyfile(DEFAULT_OUTLINE_ICON, PACKAGE_DIR / "outline.png")

    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(manifest_path, arcname="manifest.json")
        archive.write(PACKAGE_DIR / "color.png", arcname="color.png")
        archive.write(PACKAGE_DIR / "outline.png", arcname="outline.png")

    details_path = BUILD_DIR / "package-details.txt"
    details_path.write_text(
        "\n".join(
            [
                f"TEAMS_APP_ID={teams_app_id}",
                f"BOT_APP_ID={bot_app_id}",
                f"BOT_ENDPOINT={bot_endpoint}",
                f"ZIP_PATH={OUTPUT_ZIP}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Teams package generated: {OUTPUT_ZIP}")


if __name__ == "__main__":
    main()
