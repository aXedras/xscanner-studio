#!/bin/bash

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo -e "${BLUE}🚀 Starting API + Studio (pre-prod compose)...${NC}"

docker compose --env-file .env.preprod -f docker-compose.preprod.yml up -d --build

echo -e "${GREEN}✓ Compose is up${NC}"
