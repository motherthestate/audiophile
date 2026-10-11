"""Generate the stacked axonometric floor plan, assets/plan-des-salles-3d.svg.

Usage: python3 scripts/plan-3d.py [theta] [squash] [gap] > assets/plan-des-salles-3d.svg
       python3 scripts/plan-3d.py --elegant > assets/plan-des-salles-3d-elegant.svg

Floor geometry mirrors assets/plan-des-salles.svg, drawn in plan coordinates and
projected onto a tilted plane; labels and icons are placed upright at their
projected points so they stay legible. Icons: Phosphor (fill weight), MIT licence.
The elegant variant embeds Geist (assets/fonts, SIL OFL 1.1).
"""
import base64, math, os, re, sys

ELEGANT = "--elegant" in sys.argv                            # quieter variant: tone instead of line
ARGS = [a for a in sys.argv[1:] if a != "--elegant"]
THETA = float(ARGS[0]) if len(ARGS) > 0 else -28             # plan rotation, degrees
K = float(ARGS[1]) if len(ARGS) > 1 else 0.52                # vertical squash
GAP = float(ARGS[2]) if len(ARGS) > 2 else 360               # screen distance between floors
SLAB = 8 if ELEGANT else 14                                   # floor thickness, px
WALL = 10                                                     # low wall height, px
DY = -636                                                     # -1 top (868) onto RDC top (232)
CX, CY = 575, 520                                             # plan centre

t = math.radians(THETA)
A, B, C, D = math.cos(t), K * math.sin(t), -math.sin(t), K * math.cos(t)
E, F = -(A * CX + C * CY), -(B * CX + D * CY)
MAT = f"matrix({A:.5f} {B:.5f} {C:.5f} {D:.5f} {E:.3f} {F:.3f})"

def proj(x, y):
    return A * x + C * y + E, B * x + D * y + F

FLOORS = {"rdc": 0.0, "m1": GAP}  # screen y offset per floor

# Phosphor Icons 2.1.1, fill weight, viewBox 0 0 256 256
PH = {
    "elevator": "M208,32H48A16,16,0,0,0,32,48V208a16,16,0,0,0,16,16H208a16,16,0,0,0,16-16V48A16,16,0,0,0,208,32ZM112,56h32a8,8,0,0,1,0,16H112a8,8,0,0,1,0-16Zm8,152H64V96h56Zm72,0H136V96h56Z",
    "stairs": "M240,56V200a8,8,0,0,1-8,8H8a8,8,0,0,1,0-16H56V152a8,8,0,0,1,8-8h48V104a8,8,0,0,1,8-8h48V56a8,8,0,0,1,8-8h56A8,8,0,0,1,240,56Z",  # Phosphor "steps"
    "person": "M100,36a28,28,0,1,1,28,28A28,28,0,0,1,100,36ZM215.42,140.78l-45.25-51.3a28,28,0,0,0-21-9.48H106.83a28,28,0,0,0-21,9.48l-45.25,51.3a16,16,0,0,0,22.56,22.69L89,142.7l-19.7,74.88a16,16,0,0,0,29.08,13.35L128,180l29.58,51a16,16,0,0,0,29.08-13.35L167,142.7l25.9,20.77a16,16,0,0,0,22.56-22.69Z",
    "martini": "M237.66,45.66A8,8,0,0,0,232,32H24a8,8,0,0,0-5.66,13.66L120,147.31V208H88a8,8,0,0,0,0,16h80a8,8,0,0,0,0-16H136V147.31Zm-25,2.34-16,16H59.31l-16-16Z",
    "call-bell": "M16,176a8,8,0,0,1,8-8h8V152a96.12,96.12,0,0,1,88-95.66V40H104a8,8,0,0,1,0-16h48a8,8,0,0,1,0,16H136V56.34A96.12,96.12,0,0,1,224,152v16h8a8,8,0,0,1,0,16H24A8,8,0,0,1,16,176Zm216,24H24a8,8,0,0,0,0,16H232a8,8,0,0,0,0-16Z",
    "arrow-up": "M207.39,115.06A8,8,0,0,1,200,120H136v96a8,8,0,0,1-16,0V120H56a8,8,0,0,1-5.66-13.66l72-72a8,8,0,0,1,11.32,0l72,72A8,8,0,0,1,207.39,115.06Z",
    "arrow-down": "M205.66,149.66l-72,72a8,8,0,0,1-11.32,0l-72-72A8,8,0,0,1,56,136h64V40a8,8,0,0,1,16,0v96h64a8,8,0,0,1,5.66,13.66Z",
}

STYLE = """
      text { font-family: Roboto, 'Helvetica Neue', Helvetica, Arial, sans-serif; fill: #fff; }
      .h1 { font-size: 34px; font-weight: 500; letter-spacing: 1px; }
      .h2 { font-size: 30px; font-weight: 500; letter-spacing: .5px; }
      .lbl { font-size: 17px; font-weight: 500; letter-spacing: .5px; }
      .num { font-size: 26px; font-weight: 500; }
      .sm { font-size: 12px; font-weight: 500; letter-spacing: .5px; fill: #fff; }
      .wall { fill: none; stroke: #aaa196; stroke-width: 1.5; stroke-linejoin: miter; }
      .face { stroke: #16130f; stroke-width: .8; stroke-linejoin: round; }
      .face-x { fill: #9d958b; }
      .face-y { fill: #6d665e; }
      .face.outer { stroke: #e0d8cc; stroke-width: 1.2; }
      .mass { fill: #4f4943; stroke: #16130f; stroke-width: 1.5; }
      .room { fill: #9a8360; stroke: #16130f; stroke-width: 1.5; }
      .studio-a { fill: #7fcfc0; }
      .studio-b { fill: #bfa8ec; }
      .studio-c { fill: #f5a3bb; }
      .lab { fill: #f7b955; }
      .box { fill: #8db7f0; }
      .gallery { fill: #f3a07f; }
      .pill { fill: #16130f; stroke: #aaa196; stroke-width: 1; }
      .ico { fill: none; stroke: #c6bdb1; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
      .badge { fill: #fff; stroke: #16130f; stroke-width: 1.5; }
      .glyph { fill: #16130f; }
      .dir { fill: #F09818; stroke: #16130f; stroke-width: 1.5; }
      .dir-glyph { fill: #16130f; }
"""

STYLE_ELEGANT = """
      text { font-family: Geist, 'Helvetica Neue', Helvetica, Arial, sans-serif; fill: #f2f3f4; }
      .h1 { font-size: 30px; font-weight: 400; letter-spacing: 10px; }
      .h2 { font-size: 46px; font-weight: 400; letter-spacing: 4px; fill: #e6e7e9; }
      .lbl { font-size: 16px; font-weight: 500; letter-spacing: 1.5px; fill: #f2f3f4; }
      .pill { fill: #111214; fill-opacity: .86; }
      .num { font-size: 22px; font-weight: 500; letter-spacing: .5px; fill: #111214; opacity: .75; }
      .sm { font-size: 13px; font-weight: 500; letter-spacing: 2px; }
      .wall { display: none; }
      .mass { fill: #55585c; }
      .room { fill: #a7aaae; }
      .studio-a { fill: #8fb8ad; }
      .studio-b { fill: #a99cc4; }
      .studio-c { fill: #d39aa6; }
      .lab { fill: #d9a75a; }
      .box { fill: #8aa3c4; }
      .gallery { fill: #cf8f73; }
      .r203 { fill: #c9b26c; }
      .r205 { fill: #9fb9d8; }
      .r207 { fill: #c39cba; }
      .r209 { fill: #98c29f; }
      .r211 { fill: #d8ad8a; }
      .r213 { fill: #a5a9d6; }
      .r204 { fill: #b8c57b; }
      .r206 { fill: #7fb5c4; }
      .cap { fill: none; stroke: #fff; stroke-opacity: .28; stroke-width: .8; }
      .badge { fill: #f2f3f4; }
      .glyph { fill: #111214; }
      .dir { fill: #F09818; }
      .dir-glyph { fill: #111214; }
"""
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")


def font_face(weight, file):
    data = base64.b64encode(open(os.path.join(FONT_DIR, file), "rb").read()).decode()
    return f"@font-face {{ font-family: Geist; font-weight: {weight}; src: url(data:font/woff2;base64,{data}) format('woff2'); }}"


# wall base colour per room class (elegant): faces are shades of the room they bound
WALL_BASE = {"outer": "#95989c", "mass": "#63666a", "room": "#a7aaae", "studio-a": "#8fb8ad",
             "studio-b": "#a99cc4", "studio-c": "#d39aa6", "lab": "#d9a75a",
             "box": "#8aa3c4", "gallery": "#cf8f73",
             "r203": "#c9b26c", "r205": "#9fb9d8", "r207": "#c39cba", "r209": "#98c29f",
             "r211": "#d8ad8a", "r213": "#a5a9d6", "r204": "#b8c57b", "r206": "#7fb5c4"}
PRIORITY = ["mass", "room", "named", "outer"]


def shade(hex_, f):
    """Mix a colour toward black by f (0..1)."""
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(round(c * (1 - f)) for c in (r, g, b))


# ---------- in-plane content (plan coordinates; -1 shifted by DY) ----------
RDC_OUTLINE = "M140 232H1005V805H460V665H620V443H140Z"
M1_OUTLINE = "M140 232H1005V863H140Z"

RDC_PLANE = """
  <rect x="140" y="232" width="140" height="70" class="mass"/>
  <rect x="280" y="232" width="138" height="70" class="room studio-c"/>
  <rect x="418" y="232" width="69" height="70" class="mass"/>
  <rect x="487" y="232" width="48" height="70" class="room"/>
  <rect x="535" y="232" width="46" height="70" class="room"/>
  <rect x="581" y="232" width="42" height="70" class="room"/>
  <rect x="623" y="232" width="42" height="70" class="room"/>
  <rect x="665" y="232" width="40" height="70" class="room"/>
  <rect x="705" y="232" width="38" height="70" class="room"/>
  <rect x="743" y="232" width="262" height="70" class="mass"/>
  <rect x="140" y="345" width="136" height="98" class="room studio-b"/>
  <rect x="276" y="345" width="142" height="98" class="room studio-a"/>
  <rect x="418" y="345" width="62" height="98" class="mass"/>
  <rect x="480" y="345" width="50" height="98" class="room"/>
  <rect x="530" y="345" width="42" height="98" class="room"/>
  <rect x="572" y="345" width="48" height="98" class="mass"/>
  <rect x="685" y="345" width="320" height="320" class="mass"/>
  <rect x="685" y="443" width="253" height="72" class="room lab"/>
  <g class="ico">
    <rect x="492" y="700" width="26" height="30" rx="2"/>
    <rect x="492" y="742" width="26" height="30" rx="2"/>
    <path d="M482 705v20M528 705v20M482 747v20M528 747v20"/>
    <rect x="556" y="690" width="52" height="14" rx="2"/>
    <rect x="556" y="716" width="52" height="14" rx="2"/>
    <rect x="556" y="742" width="52" height="14" rx="2"/>
    <rect x="556" y="768" width="52" height="14" rx="2"/>
    <rect x="782" y="704" width="54" height="30" rx="2"/>
    <path d="M782 714h54"/>
    <path d="M700 805v-34h36v34"/>
    <path d="M982 765h22M996 758l8 7-8 7"/>
  </g>
"""

# drawn at wall-top height, above the walls
RDC_RAISED = """
  <g class="num" text-anchor="middle">
    <text transform="translate(502 267) rotate(90)">203</text>
    <text transform="translate(549 267) rotate(90)">205</text>
    <text transform="translate(593 267) rotate(90)">207</text>
    <text transform="translate(635 267) rotate(90)">209</text>
    <text transform="translate(676 267) rotate(90)">211</text>
    <text transform="translate(715 267) rotate(90)">213</text>
    <text transform="translate(496 394) rotate(90)">204</text>
    <text transform="translate(542 394) rotate(90)">206</text>
  </g>
"""

M1_PLANE = f"""
 <g transform="translate(0 {DY})">
  <rect x="140" y="868" width="865" height="70" class="mass"/>
  <rect x="140" y="981" width="432" height="98" class="mass"/>
  <rect x="572" y="981" width="48" height="98" class="mass"/>
  <rect x="685" y="981" width="320" height="98" class="mass"/>
  <rect x="140" y="1079" width="480" height="420" fill="url(#garden)" stroke="#16130f" stroke-width="1.5"/>
  <rect x="312" y="1237" width="308" height="242" class="room gallery"/>
  <path d="M685 1079H1005V1499H620V1479H620V1409H840V1474H900V1379H685Z" class="mass"/>
  <rect x="685" y="1154" width="200" height="85" class="room box"/>
 </g>
"""

# ---------- upright items: (plan x, plan y) anchor points ----------
def m1(x, y):
    return x, y + DY

# (glyph, x, y, stair direction or None)
ICONS = {
    "rdc": [("stairs", 450, 268, "down"), ("restroom", 451, 370, None), ("elevator", 596, 400, None),
            ("elevator", 727, 372, None), ("stairs", 870, 790, "down"),
            ("call-bell", 809, 712, None), ("martini", 972, 752, None)],
    "m1": [("stairs", *m1(450, 904), "up"), ("elevator", *m1(596, 1036), None),
           ("elevator", *m1(727, 1008), None), ("restroom", *m1(736, 1339), None), ("restroom", *m1(840, 1339), None),
           ("stairs", *m1(870, 1426), "up")],
}
PILLS = {
    "rdc": [(["STUDIO C"], 349, 266, 110), (["STUDIO B"], 208, 397, 120), (["STUDIO A"], 347, 394, 124),
            (["THE LAB"], 811, 479, 150)],
    "m1": [(["TERRASSE", "GARDEN"], *m1(497, 1150), 120), (["THE BOX"], *m1(786, 1196), 120),
           (["THE GALLERY"], *m1(466, 1358), 150)],
}
SMALL = {
    "rdc": [(["BAR"], 972, 780)],
    "m1": [(["ACCÈS", "RDC"], *m1(790, 1394))],
}
# vertical cores shared by both floors: lifts and the main stair
CORES = [(596, 400), (727, 372), (450, 268), (870, 790)]
# links whose ends sit at different plan points: lobby stairs (RDC) -> ACCÈS RDC stairs (-1)
LINKS = []

R = 24 if ELEGANT else 19  # badge radius

if ELEGANT:
    STYLE = STYLE_ELEGANT
    RDC_PLANE = re.sub(r'<g class="ico">.*?</g>', "", RDC_PLANE, flags=re.S)  # no furniture
    M1_PLANE = M1_PLANE.replace(' stroke="#16130f" stroke-width="1.5"', "")      # no outline on the terrace
    for n, x, y in (("203", 487, 232), ("205", 535, 232), ("207", 581, 232), ("209", 623, 232),
                    ("211", 665, 232), ("213", 705, 232), ("204", 480, 345), ("206", 530, 345)):
        RDC_PLANE = re.sub(rf'(<rect x="{x}" y="{y}" [^>]*class="room)"', rf'\1 r{n}"', RDC_PLANE)
    NUMS = [("203", 511, 267), ("205", 558, 267), ("207", 602, 267), ("209", 644, 267),
            ("211", 685, 267), ("213", 724, 267), ("204", 505, 394), ("206", 551, 394)]
    RDC_RAISED = "".join(f'<text transform="translate({x} {y}) rotate(90)" dy=".35em" text-anchor="middle" class="num">{n}</text>'
                         for n, x, y in NUMS)



def poly(d, dy=0):
    """Absolute M/H/V path -> list of points."""
    pts, x, y = [], 0, 0
    for cmd, val in re.findall(r"([MHV])\s*([-\d. ]+)", d):
        nums = [float(n) for n in val.split()]
        if cmd == "M":
            x, y = nums
        elif cmd == "H":
            x = nums[0]
        else:
            y = nums[0]
        pts.append((x, y + dy))
    return pts


def rect_edges(plane, dy):
    for x, y, w, h, cls in re.findall(r'<rect x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)" class="((?:mass|room)[^"]*)"', plane):
        x, y, w, h = float(x), float(y) + dy, float(w), float(h)
        kind = cls.split()[-1]
        for e in loop([(x, y), (x + w, y), (x + w, y + h), (x, y + h)]):
            yield (*e, kind)
    for d in re.findall(r'<path d="([MHV][^"]*Z)" class="mass"', plane):
        for e in loop(poly(d, dy)):
            yield (*e, "mass")


def loop(pts):
    for a, b in zip(pts, pts[1:] + pts[:1]):
        if a != b:
            yield a, b


def split_edges(edges):
    """Cut collinear walls at every breakpoint so each piece takes the colour of the room it bounds
    (a room's own wall wins over the outer wall, which wins over unlabelled blocks)."""
    order = {"mass": 0, "outer": 1, "room": 2}
    lines = {}
    for a, b, kind in edges:
        if a[1] == b[1]:
            key, lo, hi = ("h", a[1]), min(a[0], b[0]), max(a[0], b[0])
        else:
            key, lo, hi = ("v", a[0]), min(a[1], b[1]), max(a[1], b[1])
        lines.setdefault(key, []).append((lo, hi, kind))
    out = {}
    for (axis, c), spans in lines.items():
        cuts = sorted({v for lo, hi, _ in spans for v in (lo, hi)})
        for p, q in zip(cuts, cuts[1:]):
            m = (p + q) / 2
            kinds = [k for lo, hi, k in spans if lo <= m <= hi]
            if not kinds:
                continue
            kind = max(kinds, key=lambda k: order.get(k, 3))
            a, b = ((p, c), (q, c)) if axis == "h" else ((c, p), (c, q))
            out[(a, b)] = kind
    return out


def walls(plane, outline, dy):
    """Low extruded walls along every room edge, painted back to front."""
    def rank(kind):
        return PRIORITY.index(kind if kind in ("mass", "room", "outer") else "named")

    edges = {}
    if ELEGANT:
        edges = split_edges(list(rect_edges(plane, dy)) + [(a, b, "outer") for a, b in loop(poly(outline))])
    else:
        for a, b, kind in rect_edges(plane, dy):
            key = tuple(sorted((a, b)))
            if key not in edges or rank(kind) > rank(edges[key]):
                edges[key] = kind
        for a, b in loop(poly(outline)):
            edges[tuple(sorted((a, b)))] = "outer"
    faces = []
    for (a, b), kind in edges.items():
        (ax, ay), (bx, by) = proj(*a), proj(*b)
        horiz = a[1] == b[1]
        d = f"M{ax:.1f} {ay:.1f}L{bx:.1f} {by:.1f}L{bx:.1f} {by - WALL:.1f}L{ax:.1f} {ay - WALL:.1f}Z"
        if ELEGANT:
            fill = shade(WALL_BASE[kind], .18 if horiz else .42)
            face = (f'<path d="{d}" fill="{fill}"/>'
                    f'<path d="M{ax:.1f} {ay - WALL:.1f}L{bx:.1f} {by - WALL:.1f}" class="cap"/>')
        else:
            cls = f"face {'face-x' if horiz else 'face-y'}" + (" outer" if kind == "outer" else "")
            face = f'<path d="{d}" class="{cls}"/>'
        faces.append(((ay + by) / 2, face))
    return "".join(f for _, f in sorted(faces))


def badge(glyph, px, py, direction):
    s = 28 if ELEGANT else 23
    out = [f'<circle cx="{px:.1f}" cy="{py - R:.1f}" r="{R}" class="badge"/>',
           f'<use href="#ph-{glyph}" x="{px - s / 2:.1f}" y="{py - R - s / 2:.1f}" width="{s}" height="{s}" class="glyph"/>']
    if direction:
        ax, ay = px + R - 1, py - 2 * R + 1
        dr = 11 if ELEGANT else 10
        out.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="{dr}" class="dir"/>')
        out.append(f'<use href="#ph-arrow-{direction}" x="{ax - dr * .7:.1f}" y="{ay - dr * .7:.1f}" width="{dr * 1.4:.1f}" height="{dr * 1.4:.1f}" class="dir-glyph"/>')
    return "".join(out)


def floor(key, outline, plane, dy=0, raised=""):
    oy = FLOORS[key]
    out = [f'<g transform="translate(0 {oy:.1f})">']
    if ELEGANT:
        out.append(f'<path d="{outline}" transform="translate(0 {SLAB / 2}) {MAT}" fill="#fff" opacity=".08" filter="url(#glow)"/>')
    else:
        out.append(f'<path d="{outline}" transform="translate(0 {SLAB / 2}) {MAT}" fill="#fff" opacity=".12" filter="url(#glow)"/>')
    for i in range(SLAB, 0, -1):
        out.append(f'<path d="{outline}" transform="translate(0 {i}) {MAT}" fill="{"#35373a" if ELEGANT else "#5f5851"}"/>')
    if not ELEGANT:
        out.append(f'<path d="{outline}" transform="translate(0 {SLAB}) {MAT}" fill="none" stroke="#8b8379" stroke-width="1"/>')
    out.append(f'<g transform="{MAT}"><path d="{outline}" fill="{"#85888c" if ELEGANT else "#7b746b"}"/>{plane}<path d="{outline}" class="wall"/></g>')
    out.append(walls(plane, outline, dy))
    if raised:
        out.append(f'<g transform="translate(0 {-WALL}) {MAT}">{raised}</g>')
    for glyph, x, y, direction in ICONS[key]:
        out.append(badge(glyph, *proj(x, y), direction))
    for lines, x, y, w in PILLS[key]:
        px, py = proj(x, y)
        if ELEGANT:  # slim borderless chip sized to its text
            cw = max(len(t) for t in lines) * 11.2 + 26
            ch = 34 + 20 * (len(lines) - 1)
            out.append(f'<rect x="{px - cw / 2:.1f}" y="{py - ch / 2:.1f}" width="{cw:.0f}" height="{ch}" rx="17" class="pill"/>')
            for i, s in enumerate(lines):
                out.append(f'<text x="{px:.1f}" y="{py + 5.6 - 10 * (len(lines) - 1) + 20 * i:.1f}" text-anchor="middle" class="lbl">{s}</text>')
            continue
        h = 30 + 20 * (len(lines) - 1)
        out.append(f'<rect x="{px - w / 2:.1f}" y="{py - h / 2:.1f}" width="{w}" height="{h}" rx="15" class="pill"/>')
        for i, s in enumerate(lines):
            ty = py + 6 - 10 * (len(lines) - 1) + 20 * i
            out.append(f'<text x="{px:.1f}" y="{ty:.1f}" text-anchor="middle" class="lbl">{s}</text>')
    for lines, x, y in SMALL[key]:
        px, py = proj(x, y)
        for i, s in enumerate(lines):
            lh = 16 if ELEGANT else 14
            out.append(f'<text x="{px:.1f}" y="{py + 4 + lh * i - lh / 2 * (len(lines) - 1):.1f}" text-anchor="middle" class="sm">{s}</text>')
    out.append("</g>")
    return "\n".join(out)


EXTENTS = {"rdc": ((140, 1005), (232, 805)), "m1": ((140, 1005), (232, 863))}


def corners(key):
    xs, ys = EXTENTS[key]
    return [(px, py + FLOORS[key]) for px, py in (proj(x, y) for x in xs for y in ys)]


def level_label(key, text):
    lx, ly = min(corners(key))
    if ELEGANT:
        return (f'<path d="M{lx - 56:.1f} {ly:.1f}H{lx - 10:.1f}" stroke="#c4c6c9" stroke-opacity=".5" stroke-width=".8"/>'
                f'<text x="{lx - 72:.1f}" y="{ly + 16:.1f}" text-anchor="end" class="h2">{text}</text>')
    return f'<text x="{lx - 24:.1f}" y="{ly + 10:.1f}" text-anchor="end" class="h2">{text}</text>'


pts = corners("rdc") + corners("m1")
x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
pad = 70
side = 190 if ELEGANT else 60  # room for the level labels
top = 0 if ELEGANT else 90     # room for the title
vx, vy = x0 - pad - side, y0 - pad - top
vw, vh = (x1 - x0) + 2 * pad + side, (y1 - y0) + 2 * pad + top + SLAB + 30

cores = []
for x, y in CORES:
    px, py = proj(x, y)
    if ELEGANT:
        cores.append(f'<path d="M{px:.1f} {py + SLAB:.1f}V{py + GAP - 2 * R:.1f}" stroke="#f2f3f4" stroke-opacity=".3" stroke-width=".8"/>')
    else:
        cores.append(f'<path d="M{px:.1f} {py + SLAB:.1f}V{py + GAP - 2 * R:.1f}" stroke="#8b8379" stroke-width="1.4" stroke-dasharray="4 4"/>')

fonts = (font_face(400, "Geist-Regular.woff2") + "\n" + font_face(500, "Geist-Medium.woff2")) if ELEGANT else ""
garden = ('<rect width="14" height="14" fill="#7fa36f"/><circle cx="3.5" cy="3.5" r="1" fill="#8db07c"/><circle cx="10.5" cy="10.5" r="1" fill="#8db07c"/>'
          if ELEGANT else
          '<rect width="14" height="14" fill="#5d9a55"/><circle cx="3.5" cy="3.5" r="1.6" fill="#82c174"/><circle cx="10.5" cy="10.5" r="1.6" fill="#82c174"/>')
background = (f'<radialGradient id="bg" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="#111213"/><stop offset="1" stop-color="#08080a"/></radialGradient>'
              if ELEGANT else "")
for (ax, ay), (bx, by) in LINKS:
    (sx, sy), (ex, ey) = proj(ax, ay), proj(bx, by)
    style = ('stroke="#f2f3f4" stroke-opacity=".3" stroke-width=".8"' if ELEGANT
             else 'stroke="#8b8379" stroke-width="1.4" stroke-dasharray="4 4"')
    cores.append(f'<path d="M{sx:.1f} {sy + SLAB:.1f}L{ex:.1f} {ey + GAP - 2 * R:.1f}" {style}/>')

symbols = "\n".join(f'    <symbol id="ph-{k}" viewBox="0 0 256 256"><path d="{d}"/></symbol>' for k, d in PH.items())
# restroom pictogram built from two Phosphor "person" figures
symbols += ('\n    <symbol id="ph-restroom" viewBox="0 0 256 256">'
            f'<path d="{PH["person"]}" transform="translate(-23 46) scale(.64)"/>'
            f'<path d="{PH["person"]}" transform="translate(115 46) scale(.64)"/>'
            '<rect x="124" y="50" width="8" height="156" rx="4"/></symbol>')

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.0f} {vy:.0f} {vw:.0f} {vh:.0f}" width="{vw:.0f}" height="{vh:.0f}" role="img" aria-labelledby="t">
  <title id="t">PLAN DES SALLES</title>
  <defs>
    <style>{fonts}{STYLE}    </style>
    <pattern id="garden" width="14" height="14" patternUnits="userSpaceOnUse">{garden}</pattern>
    {background}
{symbols}
    <filter id="glow" x="-20%" y="-30%" width="140%" height="160%"><feGaussianBlur stdDeviation="22"/></filter>
  </defs>
  <rect x="{vx:.0f}" y="{vy:.0f}" width="{vw:.0f}" height="{vh:.0f}" fill="{"url(#bg)" if ELEGANT else "#24201c"}"/>
  {"" if ELEGANT else f'<text x="{vx + vw / 2:.1f}" y="{vy + 70:.1f}" text-anchor="middle" class="h1">PLAN DES SALLES</text>'}
{floor("m1", M1_OUTLINE, M1_PLANE, DY)}
{level_label("m1", "-1")}
<g>{''.join(cores)}</g>
{floor("rdc", RDC_OUTLINE, RDC_PLANE, raised=RDC_RAISED)}
{level_label("rdc", "RDC")}
</svg>
"""
sys.stdout.write(svg)
