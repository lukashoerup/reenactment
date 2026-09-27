"""Method B: the same keyframes as stills, brought to life without a video model:
sub-pixel camera move, fire-light flicker on warm areas, a light rain layer.
Writes clips/Sx_B.mp4 with the same length as the Veo clip's used section and muxes the
Veo clip's ambient sound so edit.py can cut it identically.
"""
import json, math, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS = 1920, 1080, 24
sl = json.load(open("shotlist.json"))
KF = {"S1": "S1_v1", "S2": "S2_v1", "S3": "S3_v1", "S4": "S4_v2", "S5": "S5_v1", "S6": "S6_v2", "S7": "S7_v1", "S8": "S8_v1"}
IN = {"S1": 0.6, "S2": 1.6, "S3": 1.2, "S4": 0.7, "S5": 1.5, "S6": 1.4, "S7": 1.8, "S8": 2.2}
# (zoom0, zoom1, cx0, cy0, cx1, cy1) - centre in 0..1 of the source
MOVE = {"S1": (1.00, 1.10, .50, .50, .50, .47), "S2": (1.04, 1.09, .47, .52, .52, .50),
        "S3": (1.00, 1.06, .50, .52, .48, .48), "S4": (1.12, 1.12, .44, .52, .56, .52),
        "S5": (1.02, 1.07, .50, .55, .50, .52), "S6": (1.05, 1.07, .50, .55, .52, .55),
        "S7": (1.14, 1.14, .50, .40, .50, .56), "S8": (1.05, 1.18, .55, .55, .62, .62)}

def smooth_noise(t, seed):
    r = random.Random(seed)
    return sum(math.sin(t * f * 2 * math.pi + r.random() * 6.28) * amp
               for f, amp in [(0.7, .5), (1.9, .3), (4.3, .2), (7.1, .12)])

for s in sl["shots"]:
    sid = s["id"]
    if sid == "S9": continue
    dur = IN[sid] + (s["end"] - s["start"]) + 0.1
    n = int(round(dur * FPS))
    src = Image.open(f"kf/{KF[sid]}.png").convert("RGB")
    sw, sh = src.size
    arr = np.asarray(src).astype(np.float32) / 255
    warm = np.clip((arr[..., 0] - arr[..., 2]) * 2.2, 0, 1) * np.clip(arr.mean(-1) * 1.6, 0, 1)
    warm_img = Image.fromarray((warm * 255).astype(np.uint8))
    rnd = random.Random(sid)
    drops = [[rnd.random() * W, rnd.random() * H, 30 + rnd.random() * 50, 0.3 + rnd.random() * 0.7] for _ in range(260)]
    z0, z1, cx0, cy0, cx1, cy1 = MOVE[sid]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", f"clips/{sid}_v1.mp4", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "16",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", f"clips/{sid}_B.mp4"], stdin=subprocess.PIPE)
    for i in range(n):
        u = i / max(1, n - 1)
        e = u * u * (3 - 2 * u)                      # ease in/out
        z = z0 + (z1 - z0) * e
        cx = (cx0 + (cx1 - cx0) * e) * sw; cy = (cy0 + (cy1 - cy0) * e) * sh
        # handheld: tiny smooth drift
        t = i / FPS
        cx += smooth_noise(t, sid + "x") * sw * 0.0015; cy += smooth_noise(t, sid + "y") * sh * 0.0015
        vw, vh = sw / z, sh / z
        a = vw / W; e2 = vh / H
        frame = src.transform((W, H), Image.AFFINE, (a, 0, cx - vw / 2, 0, e2, cy - vh / 2), resample=Image.BICUBIC)
        wm = warm_img.transform((W, H), Image.AFFINE, (a, 0, cx - vw / 2, 0, e2, cy - vh / 2), resample=Image.BILINEAR)
        f = np.asarray(frame).astype(np.float32)
        flick = 1 + 0.10 * smooth_noise(t * 1.6, sid + "f")
        m = np.asarray(wm).astype(np.float32)[..., None] / 255
        f = f * (1 + (flick - 1) * m)
        # rain streaks, brighter where the fire lights them
        layer = Image.new("L", (W // 2, H // 2), 0); d = ImageDraw.Draw(layer)
        for dr in drops:
            x, y, L, b = dr
            yy = (y + t * 1400 * (0.8 + b * 0.4)) % (H + 100) - 50
            d.line([(x / 2, yy / 2), (x / 2 - 2, yy / 2 + L / 2)], fill=int(90 * b), width=1)
        layer = layer.filter(ImageFilter.GaussianBlur(0.6)).resize((W, H), Image.BILINEAR)
        rain = np.asarray(layer).astype(np.float32)[..., None] / 255
        f = f + rain * (40 + 160 * m) * np.array([1.0, 0.8, 0.6])
        p.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    print(sid, n, "frames")
