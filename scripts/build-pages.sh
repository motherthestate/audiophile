#!/usr/bin/env bash
# Builds everything that gets deployed, from the full-size originals in assets/:
#
#   wp-content/uploads/2026/salon/  the image set for the live site — resized to
#                                   1800px and re-encoded as WebP. index.html
#                                   points here, so this is what goes on the
#                                   server and what the dev server hands back.
#   docs/                           the GitHub Pages preview: a full HTML
#                                   document around the WordPress fragment plus
#                                   a copy of that same image set. Pages is set
#                                   to "Deploy from a branch: main /docs", so
#                                   docs/ is committed.
#
# index.html uses the production path, /wp-content/uploads/2026/salon/, which
# resolves on audiophile.lu and against the dev server alike. Pages serves this
# repo from /audiophile/, where a root-absolute path would miss, so wrap-page.py
# drops the leading slash — the folder layout underneath docs/ is identical.
set -euo pipefail
cd "$(dirname "$0")/.."

src=assets
assets=wp-content/uploads/2026/salon
out=docs

max=1800        # the page's content column is 1140px, so this still has headroom
quality=80      # photographs
quality_art=85  # the halftone key art, whose dot pattern shows artefacts sooner

if ! command -v cwebp >/dev/null; then
  echo "build-pages: cwebp not found — install it with: brew install webp" >&2
  exit 1
fi

rm -rf "$assets" "$out" && mkdir -p "$assets" "$out"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

for f in "$src"/*; do
  b=$(basename "$f")
  case "$b" in
    # vector logos are copied as-is, there is nothing to re-encode
    *.svg) cp "$f" "$assets/$b"; continue ;;
    *.png) q=$quality_art ;;
    *)     q=$quality ;;
  esac
  # sips only ever shrinks, so anything under $max keeps its own size
  sips -Z "$max" "$f" --out "$tmp/$b" >/dev/null
  cwebp -quiet -m 6 -q "$q" "$tmp/$b" -o "$assets/${b%.*}.webp"
done

# the preview serves the very same files, one directory deeper
mkdir -p "$out/$(dirname "$assets")"
cp -R "$assets" "$out/$assets"

python3 scripts/wrap-page.py >"$out/index.html"

# without this Pages hands the folder to Jekyll, which skips files it dislikes
touch "$out/.nojekyll"

echo "→ $assets built ($(du -sh "$assets" | cut -f1)) — upload this folder to the server"
echo "→ $out built ($(du -sh "$out" | cut -f1))"
