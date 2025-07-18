#!/usr/bin/env sh
set -eu
dvt init
dvt doctor
echo "✅ integration smoke check passed"
