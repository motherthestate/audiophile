#!/usr/bin/env bash
# Builds the GitHub Pages site into docs/ — a full HTML document around the
# WordPress fragment plus web-weight copies of assets/ (max 1400px, JPEG q78).
# Pages is set to "Deploy from a branch: main /docs", so docs/ is committed.
set -euo pipefail
cd "$(dirname "$0")/.."

out=docs
rm -rf "$out" && mkdir -p "$out/assets"

for f in assets/*; do
  b=$(basename "$f")
  case "$b" in
    # vector logos are copied as-is, sips cannot rasterise them usefully
    *.svg) cp "$f" "$out/assets/$b" ;;
    # the halftone key art keeps its dot pattern only as PNG
    *.png) sips -Z 1400 "$f" --out "$out/assets/$b" >/dev/null ;;
    *)     sips -Z 1400 -s format jpeg -s formatOptions 78 "$f" --out "$out/assets/$b" >/dev/null ;;
  esac
done

python3 scripts/wrap-page.py >"$out/index.html"

# without this Pages hands the folder to Jekyll, which skips files it dislikes
touch "$out/.nojekyll"

echo "→ $out built ($(du -sh "$out" | cut -f1))"
