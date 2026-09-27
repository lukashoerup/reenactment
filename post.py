"""Post: atmosphere, rain, bloom, film look. Works on Blender EXR renders and on stock clips.

usage:
  bvenv/bin/python post.py render SHOT            # render/SHOT/*.exr -> post/SHOT/*.png
  bvenv/bin/python post.py stock SHOT CLIP START  # stock clip -> post/SHOT/*.png (length from SHOTS)
"""
import sys, os, json, math, glob
import numpy as np
import cv2
import OpenEXR

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H = 1280, 536
FPS = 24

LOOK = dict(
    exposure=1.35,
    fog_col=np.array([0.017, 0.023, 0.033], np.float32),
    fog_amt=0.88,
    glow_col=np.array([1.0, 0.42, 0.13], np.float32),
    glow_amp=0.012,
    fog_glow=0.045,
    rain=1.0,
    grain=0.022,
)


def srgb_to_lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def read_exr(path):
    with OpenEXR.File(path) as f:
        ch = f.channels()
        rgb = ch["ViewLayer.Combined"].pixels[..., :3].astype(np.float32)
        mist = ch["ViewLayer.Mist.Z"].pixels.astype(np.float32)
    if rgb.shape[1] != W:
        rgb = cv2.resize(rgb, (W, H), interpolation=cv2.INTER_CUBIC)
        rgb = np.clip(rgb + 0.35 * (rgb - cv2.GaussianBlur(rgb, (0, 0), 1.4)), 0, None)  # win back some edge
        mist = cv2.resize(mist, (W, H), interpolation=cv2.INTER_LINEAR)
    return rgb, mist


def fire_glow(fire, h=H, w=W):
    """Warm light scattered by rain and mist around the fire, from its screen position."""
    if fire is None:
        return np.zeros((h, w, 1), np.float32)
    u, v, depth = fire
    cx, cy = u * w, (1 - v) * h
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r2 = (xx - cx) ** 2 + (yy - cy) ** 2
    s1 = max(40.0, 5200.0 / max(depth, 1.0))
    s2 = s1 * 3.2
    g = 1.0 * np.exp(-r2 / (2 * s1 * s1)) + 0.35 * np.exp(-r2 / (2 * s2 * s2))
    near = 1.0 / (1.0 + 0.04 * max(depth, 0.5))
    return (g * (0.4 + 0.6 * near))[..., None].astype(np.float32)


class Rain:
    """Screen-space rain in three depth layers; streaks are lit by what is behind them."""

    def __init__(self, seed=1, wind=0.13, density=1.0):
        rnd = np.random.default_rng(seed)
        self.layers = []
        for n, length, width, alpha, speed in [
            (int(1500 * density), 16, 1, 0.050, 44),
            (int(420 * density), 38, 1, 0.085, 70),
            (int(70 * density), 90, 2, 0.11, 120),
        ]:
            x0 = rnd.uniform(-100, W + 100, n)
            y0 = rnd.uniform(0, H + 200, n)
            a = rnd.uniform(0.4, 1.0, n) * alpha
            sp = rnd.uniform(0.85, 1.15, n) * speed
            self.layers.append((x0, y0, a, sp, length, width))
        self.wind = wind

    def draw(self, frame):
        canvas = np.zeros((H, W), np.float32)
        for x0, y0, a, sp, length, width in self.layers:
            yy = (y0 + sp * frame) % (H + 200) - 100
            xx = x0 + self.wind * (sp * frame) % (W + 200) * 0 + self.wind * yy
            L = length * sp / sp.mean()
            for x, y, al, l in zip(xx, yy, a, L):
                cv2.line(canvas, (int(x * 4), int(y * 4)), (int((x - self.wind * l) * 4), int((y - l) * 4)),
                         float(al), width, lineType=cv2.LINE_AA, shift=2)
        if True:
            canvas = cv2.GaussianBlur(canvas, (0, 0), 0.6)
        return canvas


def bloom(img):
    lum = img.max(axis=2, keepdims=True)
    bright = img * np.clip(lum - 0.9, 0, None) / np.maximum(lum, 1e-4)
    out = np.zeros_like(img)
    for s, k in ((4, 0.30), (14, 0.22), (40, 0.18)):
        out += k * cv2.GaussianBlur(bright, (0, 0), s)
    # halation: red-shifted fringe
    out[..., 0] *= 1.15; out[..., 2] *= 0.7
    return out


def tonemap(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)


def film(img_lin, frame, look):
    e = img_lin * look["exposure"]
    # blend per-channel filmic with a hue-preserving curve, so fire and its reflections
    # stay orange instead of burning to white
    mx = np.maximum(e.max(axis=2, keepdims=True), 1e-5)
    hue_keep = e / mx * tonemap(mx)
    x = 0.45 * tonemap(e) + 0.55 * hue_keep
    # grade in display space: cool the shadows, keep the fire warm, pull saturation a little
    lum = (x * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(axis=2, keepdims=True)
    x = lum + (x - lum) * 0.86
    shadow = np.clip(1 - lum / 0.35, 0, 1)
    x = x + shadow * np.array([-0.006, 0.004, 0.012], np.float32)
    x = lin_to_srgb(x)
    # gentle S-curve
    x = np.clip(x, 0, 1)
    x = x + 0.10 * (x - 0.5) * (1 - np.abs(2 * x - 1))
    # vignette
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r2 = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 1.2)) ** 2
    x *= (1 - 0.28 * r2)[..., None]
    # grain, heavier in the shadows, 35mm-ish size
    rnd = np.random.default_rng(10_000 + frame)
    g = rnd.normal(0, 1, (H, W)).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 0.7) * 1.6
    lum2 = x.mean(axis=2, keepdims=True)
    x = x + g[..., None] * look["grain"] * (1.1 - 0.7 * lum2)
    # tiny black lift, like a print
    x = 0.010 + x * 0.985
    return np.clip(x, 0, 1)


def process_frame(rgb, mist, fire, frame, rain, look=LOOK, rain_gain=1.0, fog_gain=1.0):
    glow = fire_glow(fire)
    fog = look["fog_col"] + look["glow_col"] * glow[..., 0:1] * look["fog_glow"]
    m = np.clip(mist, 0, 1)[..., None] * look["fog_amt"] * fog_gain
    img = rgb * (1 - m) + fog * m
    img += look["glow_col"] * glow * look["glow_amp"] * fog_gain
    if rain is not None:
        streaks = rain.draw(frame)[..., None]
        light = cv2.GaussianBlur(img, (0, 0), 18) * 2.2 + cv2.GaussianBlur(img, (0, 0), 90) * 3.0 + look["glow_col"] * glow * 0.6 + 0.012
        img = img + streaks * light * look["rain"] * rain_gain
    img = img + bloom(img)
    return film(img, frame, look)


def write_png(path, x):
    cv2.imwrite(path, (x[..., ::-1] * 255 + 0.5).astype(np.uint8))


def do_render(shot, rain_gain=1.0):
    src = os.path.join(ROOT, "render", shot)
    out = os.path.join(ROOT, "post", shot)
    os.makedirs(out, exist_ok=True)
    meta = json.load(open(os.path.join(src, "meta.json"))) if os.path.exists(os.path.join(src, "meta.json")) else {}
    rain = Rain(seed=hash(shot) % 1000)
    files = sorted(glob.glob(os.path.join(src, "f_*.exr")))
    for i, p in enumerate(files):
        f = int(os.path.basename(p)[2:6])
        rgb, mist = read_exr(p)
        fire = meta.get(str(f))
        x = process_frame(rgb, mist, fire, f, rain, rain_gain=rain_gain)
        write_png(os.path.join(out, f"p_{i:04d}.png"), x)
    print("post", shot, len(files))


def do_stock(shot, clip, start, n_frames, gain=1.0, crop=None, zoom=(1.0, 1.0), rain_gain=1.0):
    out = os.path.join(ROOT, "post", shot)
    os.makedirs(out, exist_ok=True)
    cap = cv2.VideoCapture(clip)
    src_fps = cap.get(cv2.CAP_PROP_FPS)
    rain = Rain(seed=77, density=1.2)
    for i in range(n_frames):
        t = start + i / FPS
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * src_fps))
        ok, fr = cap.read()
        if not ok:
            break
        fr = fr[..., ::-1].astype(np.float32) / 255
        h0, w0 = fr.shape[:2]
        z = zoom[0] + (zoom[1] - zoom[0]) * i / max(1, n_frames - 1)
        tw, th = w0 / z, (w0 / z) * H / W
        cx, cy = (crop or (0.5, 0.5))
        x0 = int(np.clip(cx * w0 - tw / 2, 0, w0 - tw)); y0 = int(np.clip(cy * h0 - th / 2, 0, h0 - th))
        fr = cv2.resize(fr[y0:y0 + int(th), x0:x0 + int(tw)], (W, H), interpolation=cv2.INTER_CUBIC)
        lin = srgb_to_lin(fr) * gain
        # footage is display-referred; undo some highlight clipping so the tonemap has range
        lin = lin + np.clip(lin - 0.7, 0, None) * 2.5
        mist = np.full((H, W), 0.0, np.float32)
        x = process_frame(lin, mist, None, i, rain, rain_gain=rain_gain, fog_gain=0.0)
        write_png(os.path.join(out, f"p_{i:04d}.png"), x)
    print("post stock", shot, n_frames)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "render":
        do_render(sys.argv[2], rain_gain=float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
    elif mode == "frame":  # quick look at one exr: post.py frame path.exr out.png
        rgb, mist = read_exr(sys.argv[2])
        meta_p = os.path.join(os.path.dirname(sys.argv[2]), "meta.json")
        f = int(os.path.basename(sys.argv[2])[2:6])
        meta = json.load(open(meta_p)) if os.path.exists(meta_p) else {}
        write_png(sys.argv[3], process_frame(rgb, mist, meta.get(str(f)), f, Rain(seed=3)))
