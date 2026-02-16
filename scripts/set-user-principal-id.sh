#!/usr/bin/env sh
set -eu

if ! command -v az >/dev/null 2>&1; then
  echo "az CLI not found; skipping userPrincipalId setup"
  exit 0
fi

if ! command -v azd >/dev/null 2>&1; then
  echo "azd CLI not found; skipping userPrincipalId setup"
  exit 0
fi

user_object_id="$(az ad signed-in-user show --query id -o tsv 2>/dev/null || true)"

if [ -z "${user_object_id}" ]; then
  echo "Could not resolve signed-in user object id; userPrincipalId not updated"
  exit 0
fi

azd env set USER_PRINCIPAL_ID "${user_object_id}" >/dev/null
azd env set userPrincipalId "${user_object_id}" >/dev/null
echo "Set azd env vars USER_PRINCIPAL_ID and userPrincipalId to ${user_object_id}"