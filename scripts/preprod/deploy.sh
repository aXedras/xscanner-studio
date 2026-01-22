#!/bin/bash

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🚀 Pre-prod deploy (main → compose up)${NC}"

bash "$SCRIPT_DIR/check.sh"
bash "$SCRIPT_DIR/update-main.sh"
bash "$SCRIPT_DIR/verify-ci-main.sh" --strict
bash "$SCRIPT_DIR/database-start.sh"
bash "$SCRIPT_DIR/up.sh"
bash "$SCRIPT_DIR/health.sh"

echo -e "${GREEN}✓ Deploy complete${NC}"
