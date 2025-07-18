#!/usr/bin/env bash
set -euo pipefail
dvt init
dvt doctor
echo "✅ integration smoke check passed"
