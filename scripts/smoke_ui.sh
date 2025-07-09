#!/usr/bin/env bash
# scripts/smoke_ui.sh
set -euo pipefail

# checks that your front-end is serving Linker UI
curl -s http://localhost:5173 \
  | grep -q "<title>Linker UI</title>" \
  && echo "UI OK"
