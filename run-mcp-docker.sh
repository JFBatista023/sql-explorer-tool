#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec docker run --rm -i \
  --name sql-explorer-readonly-mcp \
  -e LOG_LEVEL="${LOG_LEVEL:-INFO}" \
  -v "${ROOT_DIR}/config.yaml:/app/config.yaml:ro" \
  sql-explorer-readonly:latest \
  python3 server.py
