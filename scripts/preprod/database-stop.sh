#!/bin/bash
# Stop Supabase (explicit; preprod-down intentionally does NOT call this)

set -euo pipefail

BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🛑 Stopping Supabase...${NC}"
supabase stop
