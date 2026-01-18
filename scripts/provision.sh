#!/usr/bin/env bash
set -euo pipefail

echo "Provisioning with azd..."
azd provision
