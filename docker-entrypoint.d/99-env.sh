#!/bin/sh
set -eu

TEMPLATE="/usr/share/nginx/html/env.template.js"
OUT="/usr/share/nginx/html/env.js"

if [ -f "$TEMPLATE" ]; then
  # envsubst is provided by gettext
  envsubst < "$TEMPLATE" > "$OUT"
fi
