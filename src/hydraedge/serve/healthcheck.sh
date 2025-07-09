#!/usr/bin/env bash
set -euo pipefail
curl -s -X GET http://localhost:8000/ping | grep -q '"pong":' && echo "OK"