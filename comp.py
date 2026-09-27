"""Filmed fire, with a wrapped bundle composited into the flames.

Shots S2, S4, S6, S7 of the cold open. Real footage does the heavy lifting:
the bundle is a dark, soft-edged shape with light-wrap and ember cracks, and
flames from a later moment of the same clip are laid back over it so the fire
burns in front of it.

usage: bvenv/bin/python comp.py SHOT [--test]
"""
import sys, os, math
import numpy as np
import cv2
import post

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = post.W, post.H, post.FPS
CLIPS = {"big": os.path.join(ROOT, "stock/hd/31352.mp4"), "tall": os.path.join(ROOT, "stock/hd/45676.mp4"),
         "sparks": os.path.join(ROOT, "stock/hd/48299.mp4")}

# (clip, start_s, zoom0, zoom1, centre(x,y) in source px, bundle (cx,cy,rx,ry) in source px or None, sparks)
SPEC = {
    "S2": ("big", 1.6, 1.12, 1.22, (500, 400), None, False),
    "S4": ("tall", 3.0, 2.05, 2.25, (575, 520), (578, 585, 78, 30), False),
    "S6": ("tall", 7.4, 2.35, 2.55, (560, 560), (570, 590, 82, 31), False),
    "S7": ("tall", 15.0, 2.9, 3.1, (590, 585), (578, 585, 78, 30), False),
}
RAIN_GAIN = {"S2": 2.6, "S4": 1.4, "S6": 1.4, "S7": 1.2}
EPISODE = {"S2": (101.9, 106.0), "S4": (108.45, 111.0), "S6": (112.8, 115.15), "S7": (115.15, 116.6)}


class Clip:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def at(self, t):
        i = int(t * self.fps) % max(1, self.n - 1)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, fr = self.cap.read()
        return post.srgb_to_lin(fr[..., ::-1].astype(np.float32) / 255)


def smooth_noise(shape, cells, seed):
    rnd = np.random.default_rng(seed)
    g = rnd.random((cells[1], cells[0])).astype(np.float32)
    return cv2.resize(g, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)


def bundle_mask(h, w, cx, cy, rx, ry, seed=5):
    """Irregular, flattened blob: a wrapped thing lying on the logs."""
    rnd = np.random.default_rng(seed)
    th = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    r = np.ones_like(th)
    for k in range(2, 8):
        r += rnd.uniform(0.02, 0.07) * np.sin(k * th + rnd.uniform(0, 6.28)) / (k ** 0.4)
    xs = cx + rx * r * np.cos(th)
    ys = cy + ry * r * np.sin(th)
    ys = np.minimum(ys, cy + ry * 0.62)          # flat underside, resting on the pile
    ss = 4
    canvas = np.zeros((h * ss, w * ss), np.uint8)
    pts = np.stack([xs * ss, ys * ss], 1).astype(np.int32)
    cv2.fillPoly(canvas, [pts], 255, lineType=cv2.LINE_AA)
    m = cv2.resize(canvas, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    return cv2.GaussianBlur(m, (0, 0), 1.6)


def comp_bundle(bg, fg, mask, t, rect, seed=5):
    """Dark mass inside the fire. No outlines: the edge is carried by the flames."""
    h, w = mask.shape
    cx, cy, rx, ry = rect
    soft = cv2.GaussianBlur(mask, (0, 0), 5)
    # uneven density: parts of the bundle are hidden by heat, smoke and logs
    dens = smooth_noise((h, w), (w // 40, h // 25), seed)
    dens2 = smooth_noise((h, w), (w // 40, h // 25), seed + 9)
    a = 0.5 + 0.5 * math.sin(t * 1.7)
    dens = 0.84 + 0.16 * (dens * a + dens2 * (1 - a))
    m = (soft * dens)[..., None]
    folds = smooth_noise((h, w), (w // 22, h // 12), seed + 3)
    body = (0.006 + 0.020 * folds[..., None]) * np.array([1.0, 0.72, 0.55], np.float32)
    # warm light bleeding round the silhouette, taken from the fire behind
    edge = np.clip(soft * (1 - soft) * 4, 0, 1)
    wrap = cv2.GaussianBlur(bg, (0, 0), 16) * cv2.GaussianBlur(edge, (0, 0), 6)[..., None] * 0.55
    out = bg * (1 - m) + (body + wrap) * m
    # flames in front, from a later moment of the same clip
    lum = fg.mean(axis=2)
    fa = np.clip((lum - 0.14) / 0.5, 0, 1) ** 1.1
    yy = np.arange(h, dtype=np.float32)[:, None]
    grad = np.clip((yy - (cy - ry * 2.0)) / (ry * 3.0), 0, 1)
    region = cv2.GaussianBlur(cv2.dilate(mask, np.ones((31, 31), np.uint8)), (0, 0), 14)
    fa = (fa * (0.35 + 0.65 * grad) * region * 0.9)[..., None]
    return out * (1 - fa) + fg * fa


def frame_region(img, z, centre):
    h0, w0 = img.shape[:2]
    tw = w0 / z
    th = tw * H / W
    x0 = float(np.clip(centre[0] - tw / 2, 0, w0 - tw))
    y0 = float(np.clip(centre[1] - th / 2, 0, h0 - th))
    return x0, y0, tw, th


def render(shot, test=False):
    clip_key, start, z0, z1, centre, rect, sparks = SPEC[shot]
    a, b = EPISODE[shot]
    n = int(round((b - a) * FPS))
    clip = Clip(CLIPS[clip_key])
    spk = Clip(CLIPS["sparks"]) if sparks else None
    out = os.path.join(ROOT, "post", shot)
    os.makedirs(out, exist_ok=True)
    rain = post.Rain(seed=hash(shot) % 97, density=1.5 if shot == "S2" else 1.2)
    h0, w0 = 720, 1280
    mask_full = bundle_mask(h0, w0, *rect) if rect else None
    frames = [n // 2] if test else range(n)
    for i in frames:
        t = start + i / FPS
        bg = clip.at(t)
        if rect:
            fg = clip.at(t + 1.73)
            bg = comp_bundle(bg, fg, mask_full, t, rect)
        if spk is not None:
            s = spk.at(t + 3.0)
            bg = bg + s * 0.6
        z = z0 + (z1 - z0) * (i / max(1, n - 1))
        x0, y0, tw, th = frame_region(bg, z, centre)
        M = np.float32([[W / tw, 0, -x0 * W / tw], [0, H / th, -y0 * H / th]])
        img = cv2.warpAffine(bg, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        img = np.clip(img, 0, None)
        # footage highlights are clipped at 1.0; give them some range back for the tonemap
        img = img * 0.8 + np.clip(img - 0.65, 0, None) * 2.2
        x = post.process_frame(img, np.zeros((H, W), np.float32), None, i, rain, rain_gain=RAIN_GAIN.get(shot, 1.25), fog_gain=0.0)
        post.write_png(os.path.join(out, f"p_{i:04d}.png") if not test else os.path.join(ROOT, "tests", f"comp_{shot}.png"), x)
    print("comp", shot, len(list(frames)))


if __name__ == "__main__":
    render(sys.argv[1], test="--test" in sys.argv)
