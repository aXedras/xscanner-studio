#!/bin/bash

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

API_URL="${PREPROD_API_URL:-http://127.0.0.1:8010/health}"

echo -e "${BLUE}🩺 Healthcheck:${NC} ${API_URL}"

if curl -fsS "$API_URL" >/dev/null; then
  echo -e "${GREEN}✓ API healthy${NC}"
  exit 0
fi

echo -e "${RED}✗ API healthcheck failed${NC}" >&2
exit 1
