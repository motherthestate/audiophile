#!/usr/bin/env python3
"""Wrap the WordPress fragment in a standalone document for GitHub Pages.

index.html is a fragment: no doctype, no <html>, no <head> — WordPress
supplies those. Served on its own it would parse in quirks mode, so the Pages
build gets a real document around it. Source of truth stays the fragment.

The fragment points at the production asset path, /wp-content/uploads/2026/
salon/, which resolves both on audiophile.lu and against the local dev server
(the files sit at that path in the repo). Pages, though, serves this repo under
/audiophile/, where a root-absolute path would miss — so here the leading slash
comes off and the same folder layout is rebuilt relative to docs/index.html.
Every raster asset is a WebP by the time build-pages.sh is done with it, so the
extensions are swapped to match; vectors are copied untouched and keep theirs.
"""

import io
import re
import sys

SRC = "index.html"
MARK = '<div id="salon26">'

# production (root-absolute) -> Pages (relative to docs/index.html)
WP_ASSETS = "/wp-content/uploads/2026/salon/"
PAGES_ASSETS = WP_ASSETS.lstrip("/")
ASSET_REF = re.compile(re.escape(WP_ASSETS) + r"([\w.-]+)(\.[A-Za-z0-9]+)")
KEEP_EXT = (".svg",)

SITE = "https://motherthestate.github.io/audiophile/"
OG_IMAGE = "https://audiophile.lu/wp-content/uploads/2026/06/landscape-2048x1073.png"
DESC = (
    "Les 24 & 25 octobre 2026, l'Audiophile transforme le Novotel Luxembourg "
    "Kirchberg en temple du Son & de l'Image : premières mondiales, systèmes de "
    "référence et démonstration Home Cinema."
)
TITLE = "Salon Hi-Fi & Home Cinema 2026 — l'Audiophile"

src = io.open(SRC, encoding="utf-8").read()
if MARK not in src:
    sys.exit("wrap-page: %r not found in %s" % (MARK, SRC))


def pages_asset(m):
    stem, ext = m.group(1), m.group(2)
    return PAGES_ASSETS + stem + (ext if ext.lower() in KEEP_EXT else ".webp")


src, found = ASSET_REF.subn(pages_asset, src)
if not found:
    sys.exit("wrap-page: no %r references in %s" % (WP_ASSETS, SRC))
if WP_ASSETS in src:
    sys.exit("wrap-page: %s has %r references this build cannot rewrite" % (SRC, WP_ASSETS))

cut = src.index(MARK)
head = src[:cut].rstrip()
body = src[cut:].rstrip()

meta = """    <link rel="canonical" href="{site}" />
    <meta name="robots" content="noindex, nofollow" />
    <meta name="description" content="{desc}" />

    <meta property="og:type" content="website" />
    <meta property="og:locale" content="fr_FR" />
    <meta property="og:site_name" content="l'Audiophile" />
    <meta property="og:url" content="{site}" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{desc}" />
    <meta property="og:image" content="{image}" />
    <meta name="twitter:card" content="summary_large_image" />""".format(
    site=SITE, desc=DESC, title=TITLE, image=OG_IMAGE
)

out = "\n".join(
    [
        "<!doctype html>",
        '<html lang="fr">',
        "  <head>",
        head,
        "",
        meta,
        "  </head>",
        "  <body>",
        body,
        "  </body>",
        "</html>",
        "",
    ]
)

sys.stdout.write(out)
