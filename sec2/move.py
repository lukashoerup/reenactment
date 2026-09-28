"""Still shots for section 2: the drawn keyframe + a slow sub-pixel camera move + subtle procedural motion.
Nothing is generated here, so nothing can morph, float or appear from nowhere:
- camera: log-zoom and pan with a gentle ease, sub-pixel (cv2.warpAffine), never showing past the drawing's edge
- rain: streaks in screen space, re-drawn 12 times a second ("on twos", like hand-drawn rain), brighter where the
  drawing is lit (rain catches light), slightly slowed so it reads as slow motion
- flicker: the orange pastel light sources (lanterns, lamps) breathe a few percent, with their cast glow
- blue: the muted blue emergency light pulses slowly like a rotating beacon
python3 sec2/move.py [ids...]        # default: every still shot with a keyframe -> sec2/clips/<id>.mp4
Each clip has HANDLE extra frames at both ends for dissolves; sec2/edit.py trims them.
"""
import json, math, os, subprocess, sys
import numpy as np, cv2

W, H, FPS, HANDLE = 1280, 720, 24, 12
SRC_W = int(W * 1.18)                       # working resolution of the keyframe (enough for zooms up to ~1.18)
shots = json.load(open("sec2/shots.json"))["shots"]
os.makedirs("sec2/clips", exist_ok=True)

def ease(t): return .45 * t + .55 * (t * t * (3 - 2 * t))

def load_kf(path):
    im = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    h, w = im.shape[:2]; tw = int(round(h * 16 / 9))
    if tw < w: x = (w - tw) // 2; im = im[:, x:x + tw]
    else: th = int(round(w * 9 / 16)); y = (h - th) // 2; im = im[y:y + th]
    return cv2.resize(im, (SRC_W, int(SRC_W * 9 / 16)), interpolation=cv2.INTER_AREA).astype(np.float32)

def masks(src):
    hsv = cv2.cvtColor(np.clip(src, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
    orange = ((h > 12) & (h < 55) & (s > .38) & (v > .45)).astype(np.float32) * np.clip((v - .45) * 3, 0, 1)
    blue = ((h > 185) & (h < 250) & (s > .16) & (v > .28)).astype(np.float32)
    lum = cv2.GaussianBlur(v, (0, 0), 25)
    return orange, blue, lum

def affine(cx, cy, z, sw, sh):
    sc = z * W / sw
    hw, hh = W / 2 / sc, H / 2 / sc                      # half view in source pixels
    px = min(max(cx * sw, hw), sw - hw); py = min(max(cy * sh, hh), sh - hh)
    return np.array([[sc, 0, W / 2 - px * sc], [0, sc, H / 2 - py * sc]], np.float32)

class Rain:
    def __init__(self, amount, seed):
        self.r = np.random.default_rng(seed); self.amount = amount
        self.layers = []
        for n, L, sp, th, al in ((int(240 * amount), (9, 16), 250, 1, .55), (int(80 * amount), (22, 38), 470, 2, .75)):
            p = np.stack([self.r.uniform(-80, W + 80, n), self.r.uniform(-60, H, n)], 1)
            self.layers.append(dict(p=p, L=self.r.uniform(*L, n), sp=sp * self.r.uniform(.85, 1.15, n), th=th,
                                    a=al * self.r.uniform(.5, 1, n)))
        self.ang = math.radians(9)
    def step(self, dt):
        for l in self.layers:
            l["p"][:, 1] += l["sp"] * dt; l["p"][:, 0] += l["sp"] * dt * math.tan(self.ang)
            out = l["p"][:, 1] - l["L"] > H
            l["p"][out, 1] = self.r.uniform(-60, -10, out.sum()); l["p"][out, 0] = self.r.uniform(-80, W + 80, out.sum())
    def draw(self):
        m = np.zeros((H * 1, W * 1), np.float32)
        for l in self.layers:
            dx, dy = math.sin(self.ang), math.cos(self.ang)
            for (x, y), L, a in zip(l["p"], l["L"], l["a"]):
                cv2.line(m, (int(x * 4), int(y * 4)), (int((x - dx * L) * 4), int((y - dy * L) * 4)), float(a), l["th"], cv2.LINE_AA, shift=2)
        return cv2.GaussianBlur(m, (0, 0), .6)

def flicker_noise(n, seed, rate=FPS / 2):
    r = np.random.default_rng(seed); t = np.arange(n) / FPS
    f = sum(np.sin(2 * math.pi * fr * t + r.uniform(0, 6.3)) * a for fr, a in ((1.3, .5), (2.9, .3), (4.7, .2)))
    k = np.floor(t * rate) / rate                              # hold on twos
    return np.interp(k, t, f)

def render(s):
    kf = f"sec2/kf/{s['id']}.png"
    if not os.path.exists(kf): print(s["id"], "no keyframe"); return
    src = load_kf(kf); sh_, sw_ = src.shape[:2]
    orange, blue, lum = masks(src)
    core_s = cv2.GaussianBlur(orange, (0, 0), 3)                 # blur once in source space, only warp per frame
    glow_s = cv2.GaussianBlur(orange, (0, 0), 40); glow_s /= glow_s.max() + 1e-6
    blue_s = cv2.GaussianBlur(blue, (0, 0), 18); blue_s /= blue_s.max() + 1e-6
    v = cv2.cvtColor(np.clip(src, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV)[..., 2].astype(np.float32) / 255
    blue_s *= np.clip((v - .22) * 2.5, 0, 1)                  # light falls on lit surfaces, not on dark silhouettes in front
    n = round(s["end"] * FPS) - round(s["start"] * FPS) + 2 * HANDLE
    if s is shots[-1]: n += round(json.load(open("sec2/shots.json"))["tail"] * FPS)   # the last shot also covers the tail
    (ax, ay, az), (bx, by, bz) = s["move"]["a"], s["move"]["b"]
    fx = s.get("fx", {}); rain = Rain(fx.get("rain", 0), sum(map(ord, s["id"])) * 7) if fx.get("rain", 0) > 0 else None
    fl = flicker_noise(n, 11 + sum(map(ord, s["id"]))) * .09 * fx.get("flicker", 0)
    dry_s = np.zeros((sh_, sw_), np.float32)                  # no rain under a roof: polygons in 0..1 keyframe coordinates
    for poly in fx.get("dry", []):
        cv2.fillPoly(dry_s, [np.array([(x * sw_, y * sh_) for x, y in poly], np.int32)], 1.0)
    if fx.get("dry"): dry_s = cv2.GaussianBlur(dry_s, (0, 0), 12)
    out = f"sec2/clips/{s['id']}.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    rm = None
    for i in range(n):
        u = ease(min(max((i - HANDLE) / max(n - 2 * HANDLE - 1, 1), -0.05), 1.05))   # handles keep moving a little
        z = math.exp(math.log(az) + (math.log(bz) - math.log(az)) * u) * 1.04   # never show the drawing's paper margin
        A = affine(ax + (bx - ax) * u, ay + (by - ay) * u, z, sw_, sh_)
        fr = cv2.warpAffine(src, A, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        if fx.get("flicker", 0) > 0:
            core = cv2.warpAffine(core_s, A, (W, H)); glow = cv2.warpAffine(glow_s, A, (W, H))
            fr = fr * (1 + fl[i] * (core * .9 + glow * .45))[..., None]
        if fx.get("blue", 0) > 0:
            b = cv2.warpAffine(blue_s, A, (W, H))
            ph = (i // 2) * 2 / FPS                                           # on twos
            pulse = max(0.0, math.cos(2 * math.pi * 0.9 * ph)) ** 3
            fr = fr + np.array([70, 105, 150], np.float32)[None, None, :] * (b * pulse * .45 * fx["blue"])[..., None]
        if rain is not None:
            if i % 2 == 0: rain.step(2 / FPS); rm = rain.draw()
            l = cv2.warpAffine(lum, A, (W, H))
            a = rm * (.16 + .75 * np.clip((l - .25) * 1.6, 0, 1))
            if fx.get("dry"): a = a * (1 - .92 * cv2.warpAffine(dry_s, A, (W, H)))
            fr = fr * (1 - a[..., None]) + np.array([236, 232, 224], np.float32)[None, None, :] * a[..., None]
        p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    print(s["id"], "->", out, n, "frames", flush=True)

if __name__ == "__main__":
    ids = sys.argv[1:]
    for s in shots:
        if s["kind"] == "still" and (not ids or s["id"] in ids): render(s)
