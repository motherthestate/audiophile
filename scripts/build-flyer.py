#!/usr/bin/env python3
"""Build the A5 room flyer for the salon as HTML, then print it to PDF.

Room copy comes verbatim from flyer/Brochure_salon_fiches_salles.docx, and the
build checks every string against it. The cover (logo, dates, venue)
is the site poster, lifted straight out of index.html so the two stay in sync.

    python3 scripts/build-flyer.py            # writes flyer/*.html, flyer/*.pdf and flyer/svg/*.svg
"""

import base64
import html
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "flyer"
HTML_OUT = OUT / "salon-2026-flyer.html"
PDF_OUT = OUT / "salon-2026-flyer-A5.pdf"
DOCX = OUT / "Brochure_salon_fiches_salles.docx"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

S, A, H = "Source", "Amplification", "Haut-parleurs"
CA, SA = "Câblage & accessoires", "Source & amplification"
HC, E = "Haut-parleurs connectés", "Électronique"
CONT = "Démonstrations en continu"


def sys_(title, rows, hours=None):
    return {"title": title, "rows": rows, "hours": hours}


STUDIO_A = {"name": "STUDIO A", "systems": [
    sys_("Système Grimm – Raidho X2.8", [(S, "Grimm Mu2"), (A, "Grimm PA1 NEW !"), (H, "Raidho X2.8 NEW !")],
         ["10h", "12h", "14h", "16h", "18h"]),
    sys_("Système Arcam – PMC", [(SA, "Arcam SA45"), (H, "PMC Prophecy 9 NEW !")],
         ["11h", "13h", "15h", "17h"]),
]}
STUDIO_B = {"name": "STUDIO B", "systems": [
    sys_("Système Wadax – D'Agostino – Estelon",
         [(S, "Wadax Studio Player – Studio PSU – Studio Clock NEW !"), (A, "D'Agostino Progression NEO Mono NEW !"),
          (H, "Estelon FORZA Ultra NEW !"), (CA, "Transparent")],
         ["10h30", "11h30", "12h30", "13h30", "14h30", "15h30", "16h30", "17h30", "18h30"]),
    sys_("Système Mark Levinson – JBL",
         [(S, "Wadax Studio Player NEW !"),
          (A, "Mark Levinson N°626 (préamplificateur) – N°636 (amplificateur de puissance)"),
          (H, "JBL Summit Makalu"), (CA, "Transparent")],
         ["10h", "11h", "12h", "13h", "14h", "15h", "16h", "17h", "18h"]),
]}
STUDIO_C = {"name": "STUDIO C", "systems": [
    sys_("Système Kii Three BXT", [(S, "Grimm MU1"), (H, "Kii Three BXT"), (CA, "Grimm")],
         ["10h30", "12h30", "14h30", "16h30", "18h30"]),
    sys_("Système MSB - Audio Analogue - Raidho",
         [(S, "MSB Palisade (Roon) NEW !"), (A, "Audio Analogue Absolute Pre + Absolute Mono"),
          (H, "Raidho TD3.10 NEW !"), (CA, "Airtech")],
         ["11h30", "13h30", "15h30", "17h30"]),
]}
GALLERY = {"name": "GALLERY 1 + 2", "systems": [
    sys_("Système LINN – B&W 801 D5",
         [(S, "Linn Klimax DSM/3"), (A, "Linn Klimax Solo 500"), (H, "B&W 801 D5 NEW !"), (CA, "HMS")],
         ["10h30", "12h", "13h30", "15h", "16h30", "18h"]),
    sys_("Système NAD Master – B&W 805 D5",
         [(SA, "NAD M66 + M23v2"), (H, "B&W 805 D5 NEW ! + 4x B&W DB2D (+ Dirac Bass Control)"), (CA, "Audioquest")],
         ["11h", "12h30", "14h", "15h30", "17h"]),
    sys_("Système Marantz Série 10 – B&W 803 D5",
         [(S, "Marantz SACD 10 + Link 10 N"), (A, "Marantz Model 10"), (H, "B&W 803 D5 NEW !"), (CA, "Audioquest")],
         ["10h", "11h30", "13h", "14h30", "16h", "17h30"]),
]}
THE_BOX = {"name": "THE BOX",
           "note": "Démonstration évolutive en continu\nStéréo 2.0 -> stéréo + 2 subwoofers 2.2 -> Surround 5.2 -> "
                   "Surround Dolby Atmos 7.4.4",
           "systems": [sys_("Système Home Cinema",
                            [("Processeur A/V", "Trinnov Altitude CI NEW !"), (A, "BLAZE + Roksan Caspian"),
                             (H, "DALI série Rubikore"), ("Subwoofers", "JL Audio E112")])]}

CHAMBRES = [
    [("kii-seven-0084-erweitert.jpg", {"name": "CHAMBRE 203", "note": CONT, "systems": [
        sys_("Système Kii Audio SEVEN", [(HC, "Kii SEVEN – enceintes actives streaming")])]}),
     ("nad-m10v3-streaming-amplifier-douglas-hifi.jpg", {"name": "CHAMBRE 204", "note": CONT, "systems": [
         sys_("Système NAD - Scansonic - JL Audio",
              [(SA, "NAD M10 V3 + Dirac Live + Dirac Bass Control"), (H, "Scansonic MB1B + 2x JL Audio D108"),
               (CA, "HMS")])]}),
     ("lyngdorf-fr2.jpg", {"name": "CHAMBRE 205", "note": CONT, "systems": [
         sys_("Système Lyngdorf 1", [(SA, "Lyngdorf TDAi 2210"), (H, "Lyngdorf FR2")]),
         sys_("Système Lyngdorf 2", [(SA, "Lyngdorf TDAi 1120"), (H, "Lyngdorf MH2 + BW2")])]})],
    [("devialet-phantom-ultimate-white.jpg", {"name": "CHAMBRE 213", "note": CONT, "systems": [
        sys_("Système 1 – DEVIALET Phantom Ultimate", [(HC, "Devialet Phantom 98dB & 108dB Ultimate stéréo")]),
        sys_("Système 2– DEVIALET Astra - JBL",
             [("Système", "Devialet Astra + JBL Summit AMA NEW !"), (CA, "Audioquest")])]}),
     ("cyrus80amprightcorner-dynamic.jpg", {"name": "CHAMBRE 206", "note": CONT, "systems": [
         sys_("Système Cyrus – Raidho", [(E, "Cyrus 80 NEW !"), (H, "Raidho X1.6 Référence NEW !")])]}),
    ],
    [("moon371shop-1200x900.jpeg", {"name": "CHAMBRE 207", "note": CONT, "systems": [
        sys_("Système Moon – Estelon", [(E, "MOON 371 NEW !"), (H, "Estelon AURA")])]}),
     ("jlaudioprimacyt6.jpg", {"name": "CHAMBRE 209", "note": CONT, "systems": [
        sys_("Système JL Audio Primacy T6", [(HC, "JL Audio Primacy T6 NEW ! – enceintes actives streaming")])]}),
     ("linn-343-single-malt.png", {"name": "CHAMBRE 211", "note": CONT, "systems": [
         sys_("Système LINN 343", [(E, "LINN Selekt DSM"), (HC, "LINN 343 NEW ! - enceinte actives streaming")])]})],
]
THE_LAB = {"name": "THE LAB", "note": "Exposition statique de matériel multimarques et démonstration casques",
           "systems": [
               sys_("Corner casques & amplis pour casques",
                    [("Marques", "Meze · Focal · Feliks Audio · Noble · Final · HiFiMAN · Questyle · Luxsin")]),
               sys_("Corner vinyle / tourne-disques", [("Marques", "Pro-Ject Audio · Transrotor · Thorens · LINN")])]}

# PLACEHOLDER — dummy text until the real intro copy arrives. Not from the docx; replace before printing.
INTRO_PLACEHOLDER = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et "
    "dolore magna aliqua.",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. "
    "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.",
]


def esc(s):
    out = html.escape(s, quote=False).replace("\n", "<br>")
    return out.replace("NEW !", '<b class="new">NEW&nbsp;!</b>')


def img(name):
    return f"../assets/{name}"


# Product cutouts on white are shown whole (contain); photos with a scene fill the frame.
CUTOUTS = {"devialet-phantom-ultimate-white.jpg", "cyrus80amprightcorner-dynamic.jpg", "transrotor-rondino.jpg"}


def thumb(name):
    cls = ' class="cutout"' if name in CUTOUTS else ""
    return f'<img{cls} src="{img(name)}" alt="">'


def poster_svgs():
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    found = re.findall(r'<svg\s+viewBox="0 0 (?:424 341|300 155)".*?</svg>', src, re.S)
    if len(found) < 2:
        sys.exit("poster SVGs not found in index.html")
    logo, dates = found[0], found[1].replace("currentColor", "#f09818")
    return logo, dates


def room_html(r):
    out = [f'<section class="room"><h2>{esc(r["name"])}</h2>']
    if r.get("note"):
        out.append(f'<p class="note">{esc(r["note"])}</p>')
    for s in r["systems"]:
        out.append(f'<div class="sys"><h3>{esc(s["title"])}</h3><dl>')
        for label, value in s["rows"]:
            out.append(f"<dt>{esc(label)}</dt><dd>{esc(value)}</dd>")
        if s["hours"]:
            out.append('<dt>Horaires des démonstrations</dt>'
                       f'<dd class="hours">{"&ensp;·&ensp;".join(s["hours"])}</dd>')
        out.append("</dl></div>")
    out.append("</section>")
    return "".join(out)


def page(body, cls="", folio=None):
    f = f'<span class="folio">{folio:02d}</span>' if folio else ""
    return f'<div class="page {cls}">{body}{f}</div>'


CSS = """
@page { size: 420pt 595pt; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff; }
body { font-family: Geist, 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #3b3d42;
       -webkit-print-color-adjust: exact; print-color-adjust: exact;
       font-variant-ligatures: none; font-feature-settings: "calt" 0, "liga" 0; }  /* Geist would draw "->" as an arrow */
.page { position: relative; width: 420pt; height: 595pt; overflow: hidden; page-break-after: always;
        break-after: page; display: flex; flex-direction: column; }
.page:last-child { page-break-after: auto; break-after: auto; }
.folio { position: absolute; right: 30pt; bottom: 18pt; font-size: 7pt; font-weight: 500;
         letter-spacing: .1em; color: #7c8088; }

/* rooms */
.content { padding: 0 30pt; display: flex; flex-direction: column; gap: 0; }
.room h2 { margin: 0; font-size: 22pt; line-height: 26pt; font-weight: 500; letter-spacing: .04em; color: #f09818; }
.room .note { margin: 2pt 0 0; font-size: 9pt; line-height: 12.5pt; color: #7c8088; }
.sys { margin-top: 11pt; }
.sys h3 { margin: 0 0 4pt; font-size: 14pt; line-height: 18pt; font-weight: 300; color: #252531; }
dl { margin: 0; display: grid; grid-template-columns: 108pt 1fr; column-gap: 10pt; row-gap: 3.5pt;
     font-size: 8.5pt; line-height: 12pt; }
dt { font-weight: 600; color: #252531; }
dd { margin: 0; }
dd.hours { font-weight: 500; color: #b0700a; }
b.new { font-weight: 600; color: #b0700a; }
.rule { height: 0; border-top: .75pt solid #e2e2e4; margin: 18pt 0; }
.hero { width: 100%; object-fit: cover; display: block; flex: none; }
.hero.cutout { object-fit: contain; background: #fff; }
.intro { padding: 44pt 30pt 0; }
.intro p { margin: 0 0 12pt; font-size: 10pt; line-height: 15.5pt; }
.intro .lead { font-size: 17pt; line-height: 23pt; font-weight: 300; color: #252531; margin-bottom: 16pt; }

/* chambres */
.chambres { padding: 34pt 30pt 0; }
.chambre { display: grid; grid-template-columns: 96pt 1fr; column-gap: 18pt; align-items: start; }
.chambre img { width: 96pt; height: 96pt; object-fit: cover; display: block; }
.chambre img.cutout { object-fit: contain; background: #fff; }
.chambre .sys:first-of-type { margin-top: 8pt; }

/* cover + back */
.dark { background: #08080a; color: #fff; }
.cover { background: #08080a url('../assets/salon-bg.png') center / cover no-repeat; }
.cover::before { content: ''; position: absolute; inset: 0;
  background: linear-gradient(98deg, rgba(4,4,6,.78) 0%, rgba(4,4,6,.42) 50%, rgba(4,4,6,0) 85%); }
.cover > * { position: absolute; }
.cover .mark { left: 36pt; top: 48pt; width: 250pt; }
.cover .dates { left: 36pt; top: 300pt; width: 176pt; }
.cover svg { display: block; width: 100%; height: auto; }
.cover .year { margin: 8pt 0 0; text-align: right; font-size: 13pt; font-weight: 500; letter-spacing: .34em;
               margin-right: -.34em; color: #f09818; }
.cover .venue { bottom: 48pt; left: 36pt; margin: 0; font-size: 13pt; line-height: 17pt; font-weight: 500; }
.back { justify-content: center; }
.back .map { width: 100%; display: block; }
"""

CHECK = """
<script>
addEventListener('load', () => {
  document.querySelectorAll('.page').forEach((p, i) => {
    const last = [...p.querySelectorAll('.content, .chambres, .intro')].pop();
    const bottom = last ? last.getBoundingClientRect().bottom - p.getBoundingClientRect().top : 0;
    p.dataset.fill = Math.round(bottom) + '/' + Math.round(p.clientHeight);
  });
});
</script>
"""


SVG_EXPORT_JS = r"""
<script>
// Rebuild each laid-out .page as an SVG with live <text> (one element per text block, one tspan per line).
addEventListener('load', () => { try {
  const PT = 0.75, n2 = v => +(v * PT).toFixed(2);
  const ctx = document.createElement('canvas').getContext('2d');
  const asc = {};
  const ascent = cs => {
    const k = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    if (!(k in asc)) { ctx.font = k; asc[k] = ctx.measureText('Hg').fontBoundingBoxAscent; }
    return asc[k];
  };
  const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const rgb = c => {
    const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const [r, g, b, a = 1] = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
    return { hex: '#' + [r, g, b].map(x => Math.round(x).toString(16).padStart(2, '0')).join(''), a };
  };
  const name = s => esc(s.replace(/\s+/g, ' ').trim().slice(0, 48));

  const out = [];
  for (const page of document.querySelectorAll('.page')) {
    const P = page.getBoundingClientRect();
    const X = x => n2(x - P.left), Y = y => n2(y - P.top);
    const W = n2(P.width), H = n2(P.height);
    const defs = [], body = []; let uid = 0;
    const pcs = getComputedStyle(page);
    const bg = rgb(pcs.backgroundColor);
    body.push(`<rect id="Fond" width="${W}" height="${H}" fill="${bg && bg.a > 0 ? bg.hex : '#ffffff'}"/>`);

    // cover: background photo + the poster's 98deg darkening gradient
    const bgUrl = pcs.backgroundImage.match(/url\("?([^")]+)"?\)/);
    if (bgUrl) {
      const im = document.getElementById('bgprobe');
      const s = Math.max(P.width / im.naturalWidth, P.height / im.naturalHeight);
      const dw = im.naturalWidth * s, dh = im.naturalHeight * s;
      const id = 'clip' + (++uid);
      defs.push(`<clipPath id="${id}"><rect width="${W}" height="${H}"/></clipPath>`);
      body.push(`<g id="Photo fond" clip-path="url(#${id})"><image xlink:href="${esc(bgUrl[1])}" x="${n2((P.width - dw) / 2)}" y="${n2((P.height - dh) / 2)}" width="${n2(dw)}" height="${n2(dh)}" preserveAspectRatio="none"/></g>`);
      const a = 98 * Math.PI / 180, len = Math.abs(W * Math.sin(a)) + Math.abs(H * Math.cos(a));
      const dx = Math.sin(a) * len / 2, dy = -Math.cos(a) * len / 2;
      defs.push(`<linearGradient id="voile" gradientUnits="userSpaceOnUse" x1="${(W / 2 - dx).toFixed(2)}" y1="${(H / 2 - dy).toFixed(2)}" x2="${(W / 2 + dx).toFixed(2)}" y2="${(H / 2 + dy).toFixed(2)}">` +
        `<stop offset="0" stop-color="#040406" stop-opacity=".78"/><stop offset=".5" stop-color="#040406" stop-opacity=".42"/><stop offset=".85" stop-color="#040406" stop-opacity="0"/></linearGradient>`);
      body.push(`<rect id="Voile" width="${W}" height="${H}" fill="url(#voile)"/>`);
    }

    // photos, honouring object-fit / object-position
    for (const img of page.querySelectorAll('img')) {
      const r = img.getBoundingClientRect(), cs = getComputedStyle(img);
      const nw = img.naturalWidth, nh = img.naturalHeight;
      const s = cs.objectFit === 'contain' ? Math.min(r.width / nw, r.height / nh) : Math.max(r.width / nw, r.height / nh);
      const dw = nw * s, dh = nh * s;
      const [px, py] = cs.objectPosition.split(' ').map(v => parseFloat(v) / 100);
      const id = 'clip' + (++uid), file = img.getAttribute('src').split('/').pop();
      defs.push(`<clipPath id="${id}"><rect x="${X(r.left)}" y="${Y(r.top)}" width="${n2(r.width)}" height="${n2(r.height)}"/></clipPath>`);
      const ibg = rgb(cs.backgroundColor);
      const fill = ibg && ibg.a > 0 ? `<rect x="${X(r.left)}" y="${Y(r.top)}" width="${n2(r.width)}" height="${n2(r.height)}" fill="${ibg.hex}"/>` : '';
      body.push(`<g id="Photo ${esc(file)}" clip-path="url(#${id})">${fill}<image xlink:href="${esc(img.getAttribute('src'))}" x="${X(r.left + (r.width - dw) * px)}" y="${Y(r.top + (r.height - dh) * py)}" width="${n2(dw)}" height="${n2(dh)}" preserveAspectRatio="none"/></g>`);
    }

    // thin rules
    for (const el of page.querySelectorAll('.rule')) {
      const r = el.getBoundingClientRect(), cs = getComputedStyle(el), c = rgb(cs.borderTopColor);
      body.push(`<rect id="Filet" x="${X(r.left)}" y="${Y(r.top)}" width="${n2(r.width)}" height="${n2(parseFloat(cs.borderTopWidth))}" fill="${c.hex}"/>`);
    }

    // poster artwork (logo, dates): copied as vectors
    for (const svg of page.querySelectorAll('svg')) {
      const r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
      const s = (r.width / vb.width) * PT;
      body.push(`<g id="${svg.closest('.mark') ? 'Logo Salon' : 'Dates'}" transform="translate(${X(r.left)} ${Y(r.top)}) scale(${s.toFixed(5)})">${svg.innerHTML.replace(/fill="currentColor"/g, 'fill="#f09818"')}</g>`);
    }

    // text: one plain <text> per line fragment / style run (no tspans — Figma's importer drops them), grouped per block
    for (const el of page.querySelectorAll('h2, h3, p, dt, dd, .folio')) {
      const frags = [];
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        const cs = getComputedStyle(node.parentElement);
        let cur = null;
        for (let i = 0; i < node.data.length; i++) {
          const rg = document.createRange(); rg.setStart(node, i); rg.setEnd(node, i + 1);
          const rc = rg.getClientRects()[0];
          if (!rc || rc.width === 0) continue;
          const top = Math.round(rc.top);
          if (!cur || cur.top !== top) { cur = { top, rcTop: rc.top, left: rc.left, str: '', cs }; frags.push(cur); }
          cur.str += node.data[i];
        }
      }
      frags.forEach((f, i) => { if (!frags[i + 1] || frags[i + 1].top !== f.top) f.str = f.str.replace(/\s+$/, ''); });
      const lines = frags.filter(f => f.str).map(f => {
        const cs = f.cs, c = rgb(cs.color), ls = parseFloat(cs.letterSpacing) || 0;
        return `<text x="${X(f.left)}" y="${Y(f.rcTop + ascent(cs))}" font-family="Geist" font-size="${n2(parseFloat(cs.fontSize))}" font-weight="${cs.fontWeight}" fill="${c.hex}"${ls ? ` letter-spacing="${n2(ls)}"` : ''}>${esc(f.str.replace(/[\u00a0\u2002]/g, ' '))}</text>`;
      });
      if (lines.length === 1) body.push(lines[0].replace('<text ', `<text id="${name(el.textContent)}" `));
      else if (lines.length) body.push(`<g id="${name(el.textContent)}">${lines.join('')}</g>`);
    }

    out.push(`<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>${defs.join('')}</defs>${body.join('')}</svg>`);
  }
  document.body.dataset.svgs = JSON.stringify(out);
} catch (e) { document.body.dataset.svgerr = e.stack; } });
</script>
"""


def build():
    logo, dates = poster_svgs()
    pages = []

    pages.append(page(
        f'<div class="mark">{logo}</div>'
        f'<div class="dates">{dates}<p class="year">2026</p></div>'
        '<p class="venue">Novotel,<br>Luxembourg-Kirchberg</p>', "dark cover"))

    lead, *rest = INTRO_PLACEHOLDER
    pages.append(page('<div class="intro">' + f'<p class="lead">{esc(lead)}</p>'
                      + "".join(f"<p>{esc(t)}</p>" for t in rest) + "</div>", folio=2))

    def hero_page(photo, height, position, room):
        cls = "hero cutout" if photo in CUTOUTS else "hero"
        return page(f'<img class="{cls}" style="height:{height}pt;object-position:{position}" src="{img(photo)}" alt="">'
                    f'<div class="content" style="padding-top:22pt">{room_html(room)}</div>', folio=len(pages) + 1)

    # one room per page, each under a large header photo
    for photo, height, position, room in [
        ("raidho-x2-8-speakers-png.jpg", 265, "50% 50%", STUDIO_A),
        ("estelon-forza-ultra-petra-gold.jpg", 265, "50% 50%", STUDIO_B),
        ("raidhotd3-10.jpg", 265, "50% 40%", STUDIO_C),
        ("b-w-801-d5-stealth-black-lifestyle-5-4x5.jpg", 150, "50% 20%", GALLERY),
        ("dali-rubikore-8-livingroom.jpg", 265, "50% 50%", THE_BOX),
    ]:
        pages.append(hero_page(photo, height, position, room))
    for rooms in CHAMBRES:
        parts = []
        for i, (photo, r) in enumerate(rooms):
            if i:
                parts.append('<div class="rule"></div>')
            parts.append(f'<div class="chambre">{thumb(photo)}{room_html(r)}</div>')
        pages.append(page(f'<div class="chambres">{"".join(parts)}</div>', folio=len(pages) + 1))
    pages.append(hero_page("transrotor-rondino.jpg", 265, "50% 50%", THE_LAB))

    pages.append(page(f'<img class="map" src="{img("plan-des-salles-3d-elegant.png")}" alt="Plan des salles">',
                      "dark back"))

    doc = ("<!doctype html><html lang=\"fr\"><head><meta charset=\"utf-8\">"
           "<title>Salon Hi-Fi &amp; Home Cinema 2026 – Salles</title>"
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600'
           '&display=block">'
           f"<style>{CSS}</style></head><body>{''.join(pages)}{CHECK}</body></html>")
    OUT.mkdir(exist_ok=True)
    HTML_OUT.write_text(doc, encoding="utf-8")


def docx_paragraphs():
    xml = zipfile.ZipFile(DOCX).read("word/document.xml").decode("utf-8")
    paras = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        p = re.sub(r"<w:(?:br|tab)/>", "<w:t> </w:t>", p)
        text = "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", p))
        if text.strip():
            paras.append(norm(html.unescape(text)))
    return paras


def norm(s):
    return re.sub(r"\s+", " ", s.replace("\u00a0", " ")).strip()


def audit():
    """Every room string must equal a docx paragraph (whitespace collapsed); every docx paragraph must be used."""
    source = docx_paragraphs()
    used = []
    rooms = [STUDIO_A, STUDIO_B, STUDIO_C, GALLERY, THE_BOX] + [r for page_ in CHAMBRES for _, r in page_] + [THE_LAB]
    for r in rooms:
        used += [r["name"]] + ([r["note"]] if r.get("note") else [])
        for s in r["systems"]:
            used.append(s["title"])
            for label, value in s["rows"]:
                used += [label, value]
            if s["hours"]:
                used += ["Horaires des démonstrations", " · ".join(s["hours"])]
    used = [norm(u) for u in used]
    missing = sorted({u for u in used if u not in source})
    unused = [p for p in source if p not in used]
    print(f"verbatim check: {len(set(used))} strings, {len(missing)} not in docx, {len(unused)} docx lines unused")
    for u in missing:
        print("  NOT IN DOCX:", u)
    for u in unused:
        print("  UNUSED DOCX:", u)


def render():
    common = [CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
              "--virtual-time-budget=8000", "--run-all-compositor-stages-before-draw"]
    subprocess.run(common + ["--no-pdf-header-footer", f"--print-to-pdf={PDF_OUT}", HTML_OUT.as_uri()],
                   check=True, capture_output=True)
    dom = subprocess.run(common + ["--window-size=560,800", "--dump-dom", HTML_OUT.as_uri()],
                         check=True, capture_output=True, text=True).stdout
    fills = re.findall(r'class="page[^"]*"[^>]*data-fill="([^"]+)"', dom)
    print("page fill (content bottom / page height, px):")
    for i, f in enumerate(fills, 1):
        used, total = map(int, f.split("/"))
        flag = "  <-- OVERFLOW" if used > total - 24 else ""
        print(f"  {i:02d}: {f}{flag}")
    print("wrote", PDF_OUT.relative_to(ROOT))


def export_svg():
    """Write flyer/svg/page-NN.svg: live text (Geist), embedded photos, poster vectors — for Figma import."""
    tmp = OUT / "_svg-export.html"
    tmp.write_text(HTML_OUT.read_text(encoding="utf-8").replace(
        "</body>", '<img id="bgprobe" src="../assets/salon-bg.png" alt="" style="display:none">' + SVG_EXPORT_JS + "</body>"),
                   encoding="utf-8")
    try:
        dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
                              "--virtual-time-budget=15000", "--window-size=560,800", "--dump-dom", tmp.as_uri()],
                             check=True, capture_output=True, text=True).stdout
    finally:
        tmp.unlink()
    m = re.search(r'data-svgs="([^"]*)"', dom)
    if not m:
        err = re.search(r'data-svgerr="([^"]*)"', dom)
        sys.exit("SVG export failed: " + (html.unescape(err.group(1)) if err else "no result"))
    svgs = json.loads(html.unescape(m.group(1)))
    svg_dir = OUT / "svg"
    svg_dir.mkdir(exist_ok=True)
    cache = {}

    def embed(match):
        src = match.group(1)
        if src not in cache:
            path = Path(unquote(urlparse(src).path)) if src.startswith("file:") else (OUT / src).resolve()
            with tempfile.TemporaryDirectory() as d:  # cap at ~300 dpi for A5 to keep files light
                small = Path(d) / (path.stem + ".jpg")
                subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "85", "-Z", "1800",
                                str(path), "--out", str(small)], check=True, capture_output=True)
                cache[src] = "data:image/jpeg;base64," + base64.b64encode(small.read_bytes()).decode()
        return f'xlink:href="{cache[src]}"'

    for i, svg in enumerate(svgs, 1):
        svg = re.sub(r'xlink:href="((?:\.\./|file:)[^"]+)"', embed, svg)
        (svg_dir / f"page-{i:02d}.svg").write_text(svg, encoding="utf-8")
    print(f"wrote {len(svgs)} SVGs to", svg_dir.relative_to(ROOT))


if __name__ == "__main__":
    audit()
    build()
    render()
    export_svg()
