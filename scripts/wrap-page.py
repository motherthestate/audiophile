#!/usr/bin/env python3
"""Wrap the WordPress fragment in a standalone document for GitHub Pages.

salon-2026.html is a fragment: no doctype, no <html>, no <head> — WordPress
supplies those. Served on its own it would parse in quirks mode, so the Pages
build gets a real document around it. Source of truth stays the fragment.
"""

import io
import sys

SRC = "salon-2026.html"
MARK = '<div id="salon26">'

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
