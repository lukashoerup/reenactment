"""Accurate maps for section 2, drawn from OpenStreetMap vector data (sec2/osm.py) in the charcoal-on-grey-paper look.
No image model is involved: every coastline, lake, forest, street and building is where OpenStreetMap has it.
Two layers share one projection: REGION (København–Køge–Ejby, ≈ 10 m/px) and CITY (Østerbro, ≈ 0.8 m/px).
Shots: t14 "region_drive" (København → south to Køge/Ejby), t20 "zoom_institute" (region → Teilumbygningen).

python3 sec2/maps.py layers        # draw both layers once -> sec2/maps/*.png (slow, cached)
python3 sec2/maps.py t14 t20       # render the shots -> sec2/clips/<id>.mp4 (1280x720, 24 fps, exact frames)
python3 sec2/maps.py still t20 8.5 # one frame for checking -> sec2/maps/check_t20_8.5.png
Font: Kalam (SIL Open Font License, Google Fonts), not committed:
  mkdir -p sec2/fonts && curl -s -o sec2/fonts/Kalam.ttf https://fonts.gstatic.com/s/kalam/v18/YA9dr0Wd4kDdMuhW.ttf
"""
import json, math, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

D = "sec2/mapdata"; M = "sec2/maps"; os.makedirs(M, exist_ok=True); os.makedirs("sec2/clips", exist_ok=True)
META = json.load(open(f"{D}/meta.json")) if os.path.exists(f"{D}/meta.json") else None
W, H, FPS = 1280, 720, 24
LAT0, LON0, R = 55.6, 12.3, 111320.0
KX = math.cos(math.radians(LAT0)) * R
FONT = "sec2/fonts/Kalam.ttf"
PAPER = np.array([186, 178, 164], np.float32)          # sampled from the drawn keyframes
INK = np.array([38, 36, 34], np.float32)
GRAPHITE = np.array([92, 88, 82], np.float32)
WATER = np.array([118, 121, 122], np.float32)
PASTEL = np.array([222, 146, 64], np.float32)           # the orange pastel used for light sources

def xy(lat, lon): return ((lon - LON0) * KX, (LAT0 - lat) * R)   # metres, y down

LAYERS = {   # name: (bbox S W N E, metres per pixel)
    "region": ((55.36, 11.80, 55.78, 12.75), 10.0),
    "city": (tuple(META["city"]) if META else (55.682, 12.5165, 55.714, 12.6165), 0.84),
}

def layer_geom(name):
    (s, w, n, e), mpp = LAYERS[name]
    x0, y0 = xy(n, w); x1, y1 = xy(s, e)
    return x0, y0, mpp, int(round((x1 - x0) / mpp)), int(round((y1 - y0) / mpp))

def load(name):
    p = f"{D}/{name}.json"
    return json.load(open(p))["elements"] if os.path.exists(p) else []

def rings(el):
    """Outer and inner rings (lists of (lat, lon)) of a way or multipolygon relation from 'out geom'."""
    if el["type"] == "way":
        return [[(g["lat"], g["lon"]) for g in el.get("geometry", [])]], []
    outer, inner = [], []
    for m in el.get("members", []):
        if "geometry" not in m: continue
        pts = [(g["lat"], g["lon"]) for g in m["geometry"] if g]
        (inner if m.get("role") == "inner" else outer).append(pts)
    return outer, inner

class Canvas:
    def __init__(self, name):
        self.x0, self.y0, self.mpp, self.w, self.h = layer_geom(name)
        rng = np.random.default_rng(7)
        lo = cv2.resize(rng.normal(0, 1, (self.h // 64 + 2, self.w // 64 + 2)).astype(np.float32), (self.w, self.h), interpolation=cv2.INTER_CUBIC)
        hi = rng.normal(0, 1, (self.h, self.w)).astype(np.float32)
        hi = cv2.GaussianBlur(hi, (0, 0), 0.8)
        self.img = PAPER[None, None, :] + (lo * 1.6 + hi * 4.0)[..., None] * np.array([1, .98, .95], np.float32)
        tooth = rng.random((self.h, self.w)).astype(np.float32)
        self.tooth = cv2.GaussianBlur(tooth, (0, 0), 0.7)          # charcoal catches only the paper's tooth
        self.rng = rng

    def px(self, pts):
        a = np.array([xy(la, lo) for la, lo in pts], np.float64)
        return np.stack([(a[:, 0] - self.x0) / self.mpp, (a[:, 1] - self.y0) / self.mpp], 1)

    def mask(self): return np.zeros((self.h, self.w), np.uint8)

    def ink(self, alpha, color, grain=0.55):
        """Lay pigment where alpha>0; grain breaks it up on the paper tooth like charcoal."""
        a = alpha.astype(np.float32)
        if grain: a = a * np.clip((self.tooth - (grain - 0.5)) * 2.2, 0.25, 1.0)
        self.img = self.img * (1 - a[..., None]) + color[None, None, :] * a[..., None]

    def jitter(self, p, amp):
        if amp <= 0 or len(p) < 2: return p
        n = len(p); t = np.linspace(0, 1, n)
        ph = self.rng.random(4) * 6.28
        dx = amp * (np.sin(t * 7 + ph[0]) * .6 + np.sin(t * 23 + ph[1]) * .4)
        dy = amp * (np.sin(t * 9 + ph[2]) * .6 + np.sin(t * 19 + ph[3]) * .4)
        return p + np.stack([dx, dy], 1)

    def lines(self, polylines, width, alpha, color, jitter=0.0, passes=1, grain=0.55):
        m = np.zeros((self.h, self.w), np.float32)
        for k in range(passes):
            layer = self.mask()
            for p in polylines:
                q = self.jitter(p, jitter) if jitter else p
                cv2.polylines(layer, [np.round(q * 4).astype(np.int32)], False, 255, max(1, int(round(width))), cv2.LINE_AA, shift=2)
            m = np.maximum(m, layer.astype(np.float32) / 255 * (alpha if k == 0 else alpha * .55))
        self.ink(m, color, grain)

    def fill(self, polys, holes=()):
        m = self.mask()
        for p in polys:
            if len(p) >= 3: cv2.fillPoly(m, [np.round(p * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
        for p in holes:
            if len(p) >= 3: cv2.fillPoly(m, [np.round(p * 4).astype(np.int32)], 0, cv2.LINE_AA, shift=2)
        return m

    def hatch(self, m, spacing, angle, width, alpha, color):
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        wob = cv2.resize(self.rng.normal(0, 1, (self.h // 40 + 2, self.w // 40 + 2)).astype(np.float32), (self.w, self.h)) * spacing * .12
        d = (xx * s - yy * c + wob) % spacing
        line = np.clip(1 - np.abs(d - spacing / 2) / (width / 2 + .5), 0, 1)
        self.ink(line * (m.astype(np.float32) / 255) * alpha, color)

    def waterlines(self, water, steps, alpha, color):
        """Hand-drawn 'waterlining': lines that follow every shore, spaced wider away from land."""
        dist = cv2.distanceTransform((water > 127).astype(np.uint8), cv2.DIST_L2, 5)
        wob = cv2.resize(self.rng.normal(0, 1, (self.h // 30 + 2, self.w // 30 + 2)).astype(np.float32), (self.w, self.h)) * 1.2
        m = np.zeros_like(dist)
        for i, d in enumerate(steps):
            m = np.maximum(m, np.clip(1 - np.abs(dist + wob - d) / 1.1, 0, 1) * (1 - i / (len(steps) + 1)))
        self.ink(m * alpha, color, grain=.5)

    def trees(self, m, spacing, r, alpha, color):
        """Little scribbled tree crowns on a jittered grid inside the mask."""
        layer = self.mask()
        ys, xs = np.mgrid[spacing // 2:self.h:spacing, spacing // 2:self.w:spacing]
        pts = np.stack([xs.ravel(), ys.ravel()], 1).astype(np.float32)
        pts += self.rng.uniform(-spacing * .45, spacing * .45, pts.shape)
        pts = pts[(pts[:, 0] >= 0) & (pts[:, 0] < self.w) & (pts[:, 1] >= 0) & (pts[:, 1] < self.h)]
        keep = m[pts[:, 1].astype(int), pts[:, 0].astype(int)] > 127
        for x, y in pts[keep]:
            rr = r * self.rng.uniform(.75, 1.25)
            cv2.ellipse(layer, (int(x * 4), int(y * 4)), (int(rr * 4), int(rr * 3.4)), self.rng.uniform(0, 180),
                        self.rng.uniform(0, 40), self.rng.uniform(290, 350), 255, 1, cv2.LINE_AA, shift=2)
        self.ink(layer.astype(np.float32) / 255 * alpha, color)

    def smudge(self, amount):
        n = cv2.resize(self.rng.normal(0, 1, (self.h // 180 + 2, self.w // 180 + 2)).astype(np.float32), (self.w, self.h),
                       interpolation=cv2.INTER_CUBIC)
        self.ink(np.clip(n * .6 + .1, 0, 1) * amount, GRAPHITE, grain=.3)

    def save(self, path):
        cv2.imwrite(path, cv2.cvtColor(np.clip(self.img, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))

def area_px(p):
    return abs(cv2.contourArea(p.astype(np.float32))) if len(p) >= 3 else 0

def seas(cv, coast_ways, seeds):
    """Sea = flood fill from known sea points, bounded by the coastline and the layer edge."""
    wall = cv.mask()
    for el in coast_ways:
        p = cv.px([(g["lat"], g["lon"]) for g in el["geometry"]])
        cv2.polylines(wall, [np.round(p).astype(np.int32)], False, 255, 3)
    sea = np.zeros((cv.h + 2, cv.w + 2), np.uint8)
    img = wall.copy()
    for la, lo in seeds:
        x, y = cv.px([(la, lo)])[0]
        if 0 <= x < cv.w and 0 <= y < cv.h and img[int(y), int(x)] == 0:
            cv2.floodFill(img, sea, (int(x), int(y)), 128)
    return ((img == 128) * 255).astype(np.uint8), wall

def draw_region():
    cv = Canvas("region")
    coast = load("region_coast")
    sea, wall = seas(cv, coast, [(55.52, 12.33), (55.66, 12.70), (55.42, 12.35), (55.75, 12.70)])
    lakes = cv.mask()
    for el in load("region_water"):
        o, i = rings(el)
        polys = [cv.px(r) for r in o if len(r) > 2]; holes = [cv.px(r) for r in i if len(r) > 2]
        polys = [p for p in polys if area_px(p) > 60]
        if polys: lakes = np.maximum(lakes, cv.fill(polys, holes))
    water = np.maximum(sea, lakes)
    def area_mask(name, min_px=0):
        m = cv.mask()
        for el in load(name):
            o, i = rings(el)
            polys = [cv.px(r) for r in o if len(r) > 2]; holes = [cv.px(r) for r in i if len(r) > 2]
            polys = [p for p in polys if area_px(p) > min_px]
            if polys: m = np.maximum(m, cv.fill(polys, holes))
        m[water > 0] = 0
        return m
    forest, urban = area_mask("region_forest"), area_mask("region_urban", 20)
    # water: a cool grey wash, then lines that follow every shore
    cv.ink(cv2.GaussianBlur(water, (0, 0), 2).astype(np.float32) / 255 * .42, WATER, grain=.25)
    cv.waterlines(water, [3, 7, 12, 18, 26, 36, 50], .75, INK)
    # towns: light graphite hatching; forests: darker tone with scribbled crowns
    cv.ink(cv2.GaussianBlur(urban, (0, 0), 1.5).astype(np.float32) / 255 * .20, GRAPHITE, grain=.35)
    cv.hatch(urban, 11, 35, 1.8, .50, GRAPHITE)
    cv.ink(cv2.GaussianBlur(forest, (0, 0), 2).astype(np.float32) / 255 * .22, GRAPHITE, grain=.4)
    cv.trees(forest, 9, 4.0, .85, INK)
    roads = [cv.px([(g["lat"], g["lon"]) for g in el["geometry"]]) for el in load("region_roads")]
    cv.lines([p for p in roads if len(p) > 1], 1.8, .38, GRAPHITE)
    cv.lines([cv.px([(g["lat"], g["lon"]) for g in el["geometry"]]) for el in coast], 3.4, .95, INK, jitter=1.4, passes=2)
    for el in load("region_water"):
        o, _ = rings(el)
        big = [cv.px(r) for r in o if len(r) > 2 and area_px(cv.px(r)) > 400]
        if big: cv.lines(big, 2.0, .85, INK, jitter=.6)
    cv.smudge(.16)
    cv.save(f"{M}/region.png")
    cv2.imwrite(f"{M}/region_water.png", water)

def draw_city():
    cv = Canvas("city")
    sea, wall = seas(cv, load("city_coast"), [(55.705, 12.612), (55.690, 12.612)])
    lakes = cv.mask()
    for el in load("city_water"):
        o, i = rings(el)
        polys = [cv.px(r) for r in o if len(r) > 2]; holes = [cv.px(r) for r in i if len(r) > 2]
        if polys: lakes = np.maximum(lakes, cv.fill(polys, holes))
    water = np.maximum(sea, lakes)
    green = cv.mask()
    for el in load("city_green"):
        o, i = rings(el)
        polys = [cv.px(r) for r in o if len(r) > 2]; holes = [cv.px(r) for r in i if len(r) > 2]
        if polys: green = np.maximum(green, cv.fill(polys, holes))
    green[water > 0] = 0
    bld = cv.mask(); outlines = []
    for el in load("city_buildings"):
        o, i = rings(el)
        polys = [cv.px(r) for r in o if len(r) > 2]
        if polys: bld = np.maximum(bld, cv.fill(polys, [cv.px(r) for r in i if len(r) > 2])); outlines += polys
    cv.ink(cv2.GaussianBlur(water, (0, 0), 2).astype(np.float32) / 255 * .42, WATER, grain=.25)
    cv.waterlines(water, [4, 10, 17, 26, 38, 52], .75, INK)
    cv.ink(cv2.GaussianBlur(green, (0, 0), 3).astype(np.float32) / 255 * .14, GRAPHITE, grain=.4)
    cv.trees(green, 22, 8.0, .75, INK)
    cv.ink(bld.astype(np.float32) / 255 * .26, GRAPHITE, grain=.35)
    cv.hatch(bld, 6, 38, 1.4, .6, INK)
    cv.lines(outlines, 1.8, .9, INK, jitter=.25)
    widths = {"motorway": 9, "trunk": 9, "primary": 8, "secondary": 7, "tertiary": 6, "unclassified": 4.5,
              "residential": 4.5, "living_street": 4, "pedestrian": 3.5, "service": 2.2}
    by_w = {}
    for el in load("city_roads"):
        p = cv.px([(g["lat"], g["lon"]) for g in el["geometry"]])
        by_w.setdefault(widths.get(el["tags"].get("highway"), 3), []).append(p)
    # streets as paper-coloured channels with a graphite edge, like a drafted street plan
    for w_, ps in sorted(by_w.items()):
        cv.lines(ps, w_ + 2.4, .55, GRAPHITE, grain=.5)
    for w_, ps in sorted(by_w.items()):
        m = cv.mask()
        for p in ps: cv2.polylines(m, [np.round(p * 4).astype(np.int32)], False, 255, max(1, int(w_)), cv2.LINE_AA, shift=2)
        cv.img = cv.img * (1 - m[..., None] / 255.0 * .92) + PAPER[None, None, :] * (m[..., None] / 255.0 * .92)
    rail = [cv.px([(g["lat"], g["lon"]) for g in el["geometry"]]) for el in load("city_rail")]
    cv.lines(rail, 2.2, .75, INK)
    hosp = [cv.px(r) for el in load("city_hospital") if el["tags"].get("name") == "Rigshospitalet" for r in rings(el)[0]]
    for p in hosp:   # dotted boundary of the hospital grounds
        seg = []
        L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
        for d in np.arange(0, L[-1], 14):
            k = np.searchsorted(L, d) - 1; k = max(0, min(k, len(p) - 2))
            f = (d - L[k]) / max(L[k + 1] - L[k], 1e-6); seg.append(p[k] + (p[k + 1] - p[k]) * f)
        m = cv.mask()
        for q in seg: cv2.circle(m, (int(q[0] * 4), int(q[1] * 4)), 8, 255, -1, cv2.LINE_AA, shift=2)
        cv.ink(m.astype(np.float32) / 255 * .8, INK)
    teilum = cv.fill([cv.px(r) for el in load("city_teilum") for r in rings(el)[0]])
    cv.save(f"{M}/city.png")
    cv2.imwrite(f"{M}/city_teilum.png", teilum)
    cv.lines([cv.px(r) for el in load("city_teilum") for r in rings(el)[0]], 2.4, .95, INK)
    cv.smudge(.12)
    cv.save(f"{M}/city.png")

# ---------------------------------------------------------------- camera + labels
def pyramid(img, levels=6):
    out = [img.astype(np.float32)]
    for _ in range(levels): out.append(cv2.pyrDown(out[-1]))
    return out

def view(pyr, name, cx, cy, vw):
    """Render the view (centre cx, cy in metres, width vw metres) from a layer pyramid with trilinear blending."""
    x0, y0, mpp, _, _ = layer_geom(name)
    s = vw / W / mpp                                   # layer pixels per screen pixel
    L = max(0.0, math.log2(max(s, 1e-6))); l0 = min(int(L), len(pyr) - 2); f = min(L - l0, 1.0) if s > 1 else 0.0
    outs = []
    for l in (l0, l0 + 1):
        sc = s / (2 ** l); px_, py_ = (cx - x0) / mpp / (2 ** l), (cy - y0) / mpp / (2 ** l)
        A = np.array([[1 / sc, 0, W / 2 - px_ / sc], [0, 1 / sc, H / 2 - py_ / sc]], np.float32)
        img = pyr[l]
        bv = (0, 0, 0, 0) if img.ndim == 3 and img.shape[2] == 4 else 0
        outs.append(cv2.warpAffine(img, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=bv))
    return outs[0] * (1 - f) + outs[1] * f

def screen(lat, lon, cx, cy, vw):
    x, y = xy(lat, lon); k = W / vw
    return (x - cx) * k + W / 2, (y - cy) * k + H / 2

def smooth(t): t = min(max(t, 0.0), 1.0); return t * t * t * (t * (t * 6 - 15) + 10)

def ramp(t, a, b): return smooth((t - a) / max(b - a, 1e-6))

class Labels:
    def __init__(self):
        self.f = {s: ImageFont.truetype(FONT, s) for s in (18, 26, 30, 34, 44)}
    def draw(self, frame, items):
        im = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)).convert("RGBA")
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        for it in items:
            a = it.get("alpha", 1.0)
            if a <= 0.01: continue
            x, y = it["xy"]; f = self.f[it.get("size", 30)]
            col = tuple(int(c) for c in it.get("color", INK)) + (int(235 * a),)
            halo = tuple(int(c) for c in PAPER) + (int(200 * a),)
            if it.get("box"):
                bw, bh = it["box"]; d.rounded_rectangle([x, y, x + bw, y + bh], 6, fill=tuple(int(c) for c in PAPER) + (int(215 * a),))
                continue
            if it.get("dot"):
                r = it.get("dot")
                d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=halo, width=2)
            if it.get("leader"):
                (lx, ly) = it["leader"]; d.line([x, y, lx, ly], fill=col, width=2)
            if it.get("text"):
                ax, ay = it.get("anchor_off", (12, -8))
                if it.get("angle"):
                    tw = d.textbbox((0, 0), it["text"], font=f); tim = Image.new("RGBA", (tw[2] + 16, tw[3] + 16), (0, 0, 0, 0))
                    ImageDraw.Draw(tim).text((8, 4), it["text"], font=f, fill=col, stroke_width=3, stroke_fill=halo)
                    tim = tim.rotate(it["angle"], resample=Image.BICUBIC, expand=True)
                    ov.alpha_composite(tim, (int(x - tim.width / 2), int(y - tim.height / 2)))
                else:
                    tx, ty = x + ax, y + ay
                    bb_ = d.textbbox((tx, ty), it["text"], font=f, anchor=it.get("anchor", "ls"))
                    if it.get("only_inside") and (bb_[0] < 16 or bb_[1] < 12 or bb_[2] > W - 16 or bb_[3] > H - 60): continue
                    if bb_[2] > W - 16: tx -= bb_[2] - (W - 16)
                    if bb_[0] < 16: tx += 16 - bb_[0]
                    if bb_[1] < 12: ty += 12 - bb_[1]
                    d.text((tx, ty), it["text"], font=f, fill=col, anchor=it.get("anchor", "ls"),
                           stroke_width=3, stroke_fill=halo)
        im.alpha_composite(ov)
        return np.asarray(im.convert("RGB")).astype(np.float32)

def scalebar(items, vw, metres, label, alpha):
    k = W / vw; L = metres * k; x0, y0 = 48, H - 46
    items.append({"xy": (x0 - 18, y0 - 36), "box": (L + 36, 52), "alpha": alpha})
    items.append({"xy": (x0, y0), "leader": (x0 + L, y0), "alpha": alpha})
    items.append({"xy": (x0, y0 - 7), "leader": (x0, y0 + 7), "alpha": alpha})
    items.append({"xy": (x0 + L, y0 - 7), "leader": (x0 + L, y0 + 7), "alpha": alpha})
    items.append({"xy": (x0 + L / 2, y0 - 12), "text": label, "size": 18, "anchor": "ms", "anchor_off": (0, 0), "alpha": alpha})

CREDIT = {"xy": (W - 24, H - 22), "text": "Kort: © OpenStreetMap-bidragydere", "size": 18, "anchor": "rs",
          "anchor_off": (0, 0), "alpha": .75}

# only the places the narration names at this point ("en skov nær Køge"); the find site itself is not marked
PLACES = {"København": (55.6867, 12.5701), "Køge": (55.4565, 12.1819)}

def place_items(cx, cy, vw, alpha, extra=()):
    it = []
    for name, (la, lo) in PLACES.items():
        if name in extra: continue
        x, y = screen(la, lo, cx, cy, vw)
        it.append({"xy": (x, y), "dot": 6, "text": name, "size": 34, "alpha": alpha})
    x, y = screen(55.525, 12.33, cx, cy, vw)
    it.append({"xy": (x, y), "text": "Køge Bugt", "size": 30, "anchor": "ms", "anchor_off": (0, 0),
               "alpha": alpha * .85, "color": GRAPHITE * .8})
    return it

def centroid(el_list, name, fallback):
    pts = [p for el in el_list if el.get("tags", {}).get("name") == name for r in rings(el)[0] for p in r]
    if not pts: return fallback
    a = np.array(pts); return a[:, 0].mean(), a[:, 1].mean()

def shot_frames(sid, n):
    """Yield n frames for the map shot."""
    lab = Labels()
    if sid == "t14":   # "…så jeg kørte selvfølgelig derned": København, then slowly south-west along Køge Bugt to Køge and Ejby
        reg = pyramid(cv2.cvtColor(cv2.imread(f"{M}/region.png"), cv2.COLOR_BGR2RGB))
        a = np.array(xy(55.655, 12.47)); b = np.array(xy(55.505, 12.215)); vw0, vw1 = 30000, 27000
        for i in range(n):
            t = i / max(n - 1, 1); e = t * t * (3 - 2 * t)
            c = a + (b - a) * e; vw = vw0 + (vw1 - vw0) * e
            fr = view(reg, "region", c[0], c[1], vw)
            items = place_items(c[0], c[1], vw, 1.0)
            scalebar(items, vw, 5000, "5 km", 1.0); items.append(CREDIT)
            yield lab.draw(fr, items)
    elif sid == "t20":   # region → Østerbro → Teilumbygningen, synced to the narration's place names
        reg = pyramid(cv2.cvtColor(cv2.imread(f"{M}/region.png"), cv2.COLOR_BGR2RGB))
        city = pyramid(cv2.cvtColor(cv2.imread(f"{M}/city.png"), cv2.COLOR_BGR2RGB))
        teil = pyramid(cv2.imread(f"{M}/city_teilum.png", cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255)
        tgt = np.array(xy(55.69815, 12.56625)); start = np.array(xy(55.578, 12.33))
        vw0, vw1, vwend = 52000, 1500, 1350
        green = load("city_green"); hosp = load("city_hospital")
        faelled = centroid(green, "Fælledparken", (55.7005, 12.5705)); rigs = centroid(hosp, "Rigshospitalet", (55.6955, 12.5665))
        fv = [el for el in load("city_roads") if el["tags"].get("name") == "Frederik V's Vej" and el["tags"].get("highway") == "residential"]
        fvp = np.array([(g["lat"], g["lon"]) for g in fv[0]["geometry"]]) if fv else None
        osterbro = (55.7051, 12.5826)                          # OSM place=suburb node
        p0 = np.array([(tgt[0] - start[0]) / vw0 * W + W / 2, (tgt[1] - start[1]) / vw0 * W + H / 2])   # target on screen at start
        mid = np.array([W / 2 - 60, H / 2 + 10])               # where it ends (a little left, room for the label)
        for i in range(n):
            t = i / FPS
            z = smooth((t - 0.6) / 7.6)                         # zoom runs 0.6 s → 8.2 s, then a slow settle
            lw = math.log(vw0) + (math.log(vw1) - math.log(vw0)) * z
            vw = math.exp(lw) * (1 - 0.10 * ramp(t, 8.0, 10.5))
            ps = p0 + (mid - p0) * smooth(z * 1.15)             # the target glides to the middle while we zoom in on it
            c = tgt - (ps - np.array([W / 2, H / 2])) * vw / W
            fr_r = view(reg, "region", c[0], c[1], vw) if vw > 3800 else None
            fr_c = view(city, "city", c[0], c[1], vw) if vw < 6200 else None
            wc = ramp(-math.log(vw), -math.log(6000), -math.log(4000))
            fr = fr_c if fr_r is None else fr_r if fr_c is None else fr_r * (1 - wc) + fr_c * wc
            # the Teilum building takes the orange pastel as the narrator names it
            glow = view(teil, "city", c[0], c[1], vw) * ramp(t, 7.6, 8.8) * wc
            g = cv2.GaussianBlur(glow, (0, 0), 1.2)[..., None] * .78
            fr = fr * (1 - g) + PASTEL[None, None, :] * g
            ra = 1 - ramp(-math.log(vw), -math.log(16000), -math.log(9000))
            items = place_items(c[0], c[1], vw, ra) if ra > 0 else []
            ca = ramp(t, 4.2, 5.2) * wc
            if ca > 0:
                x, y = screen(*osterbro, c[0], c[1], vw)
                items.append({"xy": (x, y), "text": "Ø S T E R B R O", "size": 30, "anchor": "ms", "anchor_off": (0, 0), "only_inside": True,
                              "alpha": ca * .8, "color": GRAPHITE * .75})
                x, y = screen(*faelled, c[0], c[1], vw)
                items.append({"xy": (x, y), "text": "Fælledparken", "size": 26, "anchor": "ms", "anchor_off": (0, 0), "alpha": ca * .9})
            if fvp is not None:
                fa = ramp(t, 3.6, 4.6) * wc
                m_ = len(fvp) // 2; p0 = screen(*fvp[max(m_ - 1, 0)], c[0], c[1], vw); p1 = screen(*fvp[min(m_ + 1, len(fvp) - 1)], c[0], c[1], vw)
                ang = -math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
                if ang > 90: ang -= 180
                if ang < -90: ang += 180
                mx, my = screen(*fvp[m_], c[0], c[1], vw)
                dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L_ = math.hypot(dx, dy) or 1; nx, ny = -dy / L_, dx / L_
                tx_, ty_ = screen(55.69815, 12.56625, c[0], c[1], vw)
                if (tx_ - mx) * nx + (ty_ - my) * ny > 0: nx, ny = -nx, -ny     # point away from Teilumbygningen
                items.append({"xy": (mx + nx * 24, my + ny * 24), "text": "Frederik V's Vej", "size": 26, "angle": ang, "alpha": fa})
            ra2 = ramp(t, 6.2, 7.2) * wc
            if ra2 > 0:
                x, y = screen(55.69833, 12.56646, c[0], c[1], vw)
                items.append({"xy": (x + 150, y - 110), "leader": (x + 14, y - 10), "text": "Retsmedicinsk Institut",
                              "size": 34, "anchor": "ls", "anchor_off": (8, -6), "alpha": ra2})
            rh = ramp(t, 9.4, 10.2) * wc
            if rh > 0:
                x, y = screen(*rigs, c[0], c[1], vw)
                items.append({"xy": (x, y + 40), "text": "Rigshospitalet", "size": 30, "anchor": "ms", "anchor_off": (0, 0), "alpha": rh})
            sb = ramp(t, 8.6, 9.4)
            if sb > 0: scalebar(items, vw, 200, "200 m", sb)
            items.append(CREDIT)
            yield lab.draw(fr, items)

def render(sid):
    sh = {s["id"]: s for s in json.load(open("sec2/shots.json"))["shots"]}[sid]
    n = round(sh["end"] * FPS) - round(sh["start"] * FPS)
    out = f"sec2/clips/{sid}.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fr in shot_frames(sid, n):
        p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    print(sid, "->", out, n, "frames")

if __name__ == "__main__":
    if sys.argv[1] == "layers":
        draw_region(); print("region done", flush=True); draw_city(); print("city done")
    elif sys.argv[1] == "still":
        sid, ts = sys.argv[2], [float(x) for x in sys.argv[3:]]
        sh = {s["id"]: s for s in json.load(open("sec2/shots.json"))["shots"]}[sid]
        n = round(sh["end"] * FPS) - round(sh["start"] * FPS); want = {min(int(t * FPS), n - 1): t for t in ts}
        for i, fr in enumerate(shot_frames(sid, n)):
            if i in want:
                cv2.imwrite(f"{M}/check_{sid}_{want[i]:.1f}.png", cv2.cvtColor(np.clip(fr, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
            if i >= max(want): break
    else:
        for sid in sys.argv[1:]: render(sid)
