#!/usr/bin/env bash
# Builds a web-weight copy of assets/ into preview/assets/ (max 1400px, JPEG q78)
# so the page can be previewed without pushing 18 MB of originals.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf preview && mkdir -p preview/assets
for f in assets/*; do
  b=$(basename "$f")
  case "$b" in
    *.png) sips -Z 1400 "$f" --out "preview/assets/$b" >/dev/null ;;
    *)     sips -Z 1400 -s format jpeg -s formatOptions 78 "$f" --out "preview/assets/$b" >/dev/null ;;
  esac
done
cp salon-2026.html preview/
echo "→ preview/ built ($(du -sh preview/assets | cut -f1))"
