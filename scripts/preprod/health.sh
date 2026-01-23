#!/bin/bash

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

API_URL="${PREPROD_API_URL:-http://127.0.0.1:8010/health}"

MAX_ATTEMPTS="${PREPROD_HEALTH_MAX_ATTEMPTS:-30}"
SLEEP_SECONDS="${PREPROD_HEALTH_SLEEP_SECONDS:-1}"

echo -e "${BLUE}🩺 Healthcheck:${NC} ${API_URL}"

last_error=""
for ((i=1; i<=MAX_ATTEMPTS; i++)); do
  if curl -fsS --connect-timeout 2 --max-time 5 "$API_URL" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ API healthy${NC}"
    exit 0
  fi

  last_error="$(curl -fsS --connect-timeout 2 --max-time 5 "$API_URL" 2>&1 || true)"
  echo -e "${BLUE}Waiting:${NC} API not ready yet (attempt ${i}/${MAX_ATTEMPTS})"
  sleep "$SLEEP_SECONDS"
done

echo -e "${RED}✗ API healthcheck failed${NC}" >&2
if [ -n "$last_error" ]; then
  echo -e "${RED}Last error:${NC} ${last_error}" >&2
fi
exit 1
