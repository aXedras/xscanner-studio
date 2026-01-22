#!/bin/bash
# Start or check Supabase for pre-prod deployments

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

if supabase status >/dev/null 2>&1; then
  echo -e "${GREEN}✓ Supabase is already running${NC}"
  exit 0
fi

echo -e "${BLUE}🚀 Starting Supabase...${NC}"
supabase start
