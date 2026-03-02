# Teams App Package

This folder contains tooling to build a Microsoft Teams app package (`.zip`) for direct upload to Teams.

## Build

From `agents/50-pb-teams-bing-agent`:

```bash
python3 teams/build_teams_package.py
```

or

```bash
make teams-package
```

Output zip:

- `teams/build/teams-app-package.zip`

Metadata file:

- `teams/build/package-details.txt`

## What it uses

- `MICROSOFT_APP_ID` from `.env`
- `BOT_ENDPOINT` from `.env` (required)
- `TEAMS_APP_ID` from `.env` (optional, for stable app id)
- default icons from `teams/default-color-icon.png` and `teams/default-outline-icon.png`

## Upload in Teams client

1. Open Teams.
2. Go to **Apps**.
3. Choose **Manage your apps** (or **Upload an app**).
4. Select **Upload a custom app**.
5. Pick `teams/build/teams-app-package.zip`.
6. Install to personal scope or add to a team/chat.

If your tenant blocks custom app uploads, ask your Teams admin to allow custom app upload or publish this package to your org catalog.
