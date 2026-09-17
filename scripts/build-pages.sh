#!/usr/bin/env bash
# Builds the GitHub Pages site into docs/ — a full HTML document around the
# WordPress fragment plus web-weight copies of the assets: max 1400px, WebP.
# Pages is set to "Deploy from a branch: main /docs", so docs/ is committed.
#
# index.html points at the production path, /wp-content/uploads/2026/salon/.
# Pages serves this repo from /audiophile/, so a root-absolute path would miss;
# wrap-page.py drops the leading slash (and swaps the extensions for .webp) and
# the assets keep the same folder layout underneath docs/.
set -euo pipefail
cd "$(dirname "$0")/.."

assets=wp-content/uploads/2026/salon
out=docs

quality=80      # photographs
quality_art=85  # the halftone key art, whose dot pattern shows artefacts sooner

if ! command -v cwebp >/dev/null; then
  echo "build-pages: cwebp not found — install it with: brew install webp" >&2
  exit 1
fi

rm -rf "$out" && mkdir -p "$out/$assets"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

for f in "$assets"/*; do
  b=$(basename "$f")
  case "$b" in
    # vector logos are copied as-is, there is nothing to re-encode
    *.svg) cp "$f" "$out/$assets/$b"; continue ;;
    *.png) q=$quality_art ;;
    *)     q=$quality ;;
  esac
  # sips only ever shrinks, so anything under 1400px keeps its own size
  sips -Z 1400 "$f" --out "$tmp/$b" >/dev/null
  cwebp -quiet -m 6 -q "$q" "$tmp/$b" -o "$out/$assets/${b%.*}.webp"
done

python3 scripts/wrap-page.py >"$out/index.html"

# without this Pages hands the folder to Jekyll, which skips files it dislikes
touch "$out/.nojekyll"

echo "→ $out built ($(du -sh "$out" | cut -f1))"
