#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "Supabase:"
supabase status || true
echo ""
echo "Compose:"
docker compose --env-file .env.preprod -f docker-compose.preprod.yml ps
