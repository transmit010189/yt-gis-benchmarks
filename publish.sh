#!/usr/bin/env bash
# Commit everything and push to GitHub. Usage: ./publish.sh "EP27: ..."
set -euo pipefail
msg="${1:-update}"
git add -A
git commit -m "$msg" || echo "(nothing to commit)"
GIT_TERMINAL_PROMPT=0 git push origin main
echo "pushed -> https://github.com/transmit010189/yt-gis-benchmarks"
