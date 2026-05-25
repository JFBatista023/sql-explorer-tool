#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}"

exec docker run --rm -i \
  --name sql-explorer-readonly-mcp \
  -e LOG_LEVEL="${LOG_LEVEL:-INFO}" \
  -e LOG_FILE="/logs/mcp.log" \
  -v "${ROOT_DIR}/config.yaml:/app/config.yaml:ro" \
  -v "${LOG_DIR}:/logs" \
  sql-explorer-readonly:latest \
  python3 server.py
