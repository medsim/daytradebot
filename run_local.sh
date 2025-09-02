#!/usr/bin/env bash
set -euo pipefail
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs -d '\n' -I {} echo {})
fi
python -m bot_daytrade.main
