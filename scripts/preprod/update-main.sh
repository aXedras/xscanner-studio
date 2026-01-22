#!/bin/bash

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo -e "${BLUE}🔄 Updating main branch...${NC}"
git fetch origin main
git checkout main
git pull --ff-only origin main

echo -e "${GREEN}✓ Updated to:${NC} $(git rev-parse --short HEAD)"
