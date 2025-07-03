#!/usr/bin/env bash
set -euo pipefail
curl -s http://localhost:5173 | grep -q "<title>Linker UI</title>" && echo "UI OK"