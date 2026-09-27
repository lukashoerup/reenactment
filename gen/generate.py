"""Generate the cold open with image and video models on fal.ai.

Stages (run in order; each is resumable, state lives in gen/<style>/state.json):
  preflight              check the key, ffmpeg and the budget without spending
  keys  STYLE [--n 4]    keyframe candidates per shot; S1 sets the look, the rest are made from it
  sheet STYLE            contact sheets per shot -> gen/<style>/sheets/
  pick  STYLE SHOT I     choose candidate I for SHOT (or: pick STYLE auto)
  clips STYLE [--takes 2] image-to-video for every picked keyframe
  take  STYLE SHOT I     choose take I (or: take STYLE auto)
  frames STYLE           chosen takes -> post/<SHOT>/p_*.png with the house film look
Then: python3 assemble.py out.mp4

Env: FAL_KEY (required), MAX_USD (default 30), IMAGE_MODEL, VIDEO_MODEL.
Never print or log the key.
"""
import os, sys, json, time, base64, subprocess, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOTS = json.load(open(os.path.join(HERE, "shots.json")))
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "fal-ai/nano-banana-2")
EDIT_MODEL = IMAGE_MODEL + "/edit"
VIDEO_MODEL = os.environ.get("VIDEO_MODEL", "fal-ai/kling-video/v3/pro/image-to-video")
PRICE = {"image": 0.12, "video_s": 0.112}  # USD: nano-banana-2 at 2K; Kling 3.0 Pro without audio (Sep 2026)
MAX_USD = float(os.environ.get("MAX_USD", "30"))
QUEUE = "https://queue.fal.run/"


# ----------------------------------------------------------------------------- fal
def _key():
    k = os.environ.get("FAL_KEY")
    if not k:
        raise SystemExit("FAL_KEY is not set. Add it as an environment variable; never paste it into chat or files.")
    return k


def _req(url, payload=None, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
    r.add_header("Authorization", "Key " + _key())
    r.add_header("Content-Type", "application/json")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(r, timeout=120) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:400]
            if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(4 * (attempt + 1)); continue
            raise SystemExit(f"fal {e.code} on {url.split('?')[0]}: {body}")
        except urllib.error.URLError:
            if attempt < 4:
                time.sleep(4 * (attempt + 1)); continue
            raise


def run(model, payload, timeout=1200):
    sub = _req(QUEUE + model, payload)
    t0 = time.time()
    while True:
        st = _req(sub["status_url"])
        if st.get("status") == "COMPLETED":
            return _req(sub["response_url"])
        if time.time() - t0 > timeout:
            raise SystemExit(f"timeout waiting for {model}")
        time.sleep(4)


def download(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    urllib.request.urlretrieve(url, path)
    return path


# ----------------------------------------------------------------------------- state
def sdir(style):
    d = os.path.join(HERE, style); os.makedirs(d, exist_ok=True); return d


def load(style):
    p = os.path.join(sdir(style), "state.json")
    return json.load(open(p)) if os.path.exists(p) else {"spent": 0.0, "shots": {}}


def save(style, st):
    json.dump(st, open(os.path.join(sdir(style), "state.json"), "w"), indent=1)


def spend(st, usd, what):
    if st["spent"] + usd > MAX_USD:
        raise SystemExit(f"budget: {what} would take spend to ${st['spent'] + usd:.2f} > MAX_USD ${MAX_USD:.2f}")
    st["spent"] += usd


def prompt(style, shot, kind):
    s = SHOTS["styles"][style]
    if kind == "key":
        return f"{s['look']} {s['cast']} {shot['key']}"
    return f"{shot['move']} {s['motion']}"


# ----------------------------------------------------------------------------- stages
def preflight():
    ok = True
    print("FAL_KEY set:", bool(os.environ.get("FAL_KEY")))
    ok &= bool(os.environ.get("FAL_KEY"))
    print("ffmpeg:", bool(subprocess.run(["which", "ffmpeg"], capture_output=True).stdout))
    print("episode audio:", os.path.exists(os.path.join(ROOT, "audio/episode.mp3")))
    n = len(SHOTS["shots"])
    est = n * 4 * PRICE["image"] + n * 2 * 5 * PRICE["video_s"]
    print(f"estimate per style: {n} shots x 4 keys + 2 takes x 5 s = ${est:.2f} (cap MAX_USD=${MAX_USD:.0f})")
    if not ok:
        raise SystemExit(1)


def keys(style, n=4):
    st = load(style)
    ref = None
    for shot in SHOTS["shots"]:
        sid = shot["id"]
        rec = st["shots"].setdefault(sid, {})
        if rec.get("keys"):
            if sid == "S1" and "pick" in rec:
                ref = rec["keys"][rec["pick"]]["url"]
            continue
        if sid != "S1" and ref is None:
            raise SystemExit("pick the S1 keyframe first: it sets the look for every other shot")
        spend(st, n * PRICE["image"], f"{n} keys for {sid}")
        p = prompt(style, shot, "key")
        if sid == "S1":
            res = run(IMAGE_MODEL, {"prompt": p, "num_images": n, "aspect_ratio": "16:9", "resolution": "2K",
                                    "output_format": "png"})
        else:
            res = run(EDIT_MODEL, {"prompt": "Same place, same two children, same clothes, same rain, light and film "
                                             "look as the reference image. New shot: " + p,
                                   "image_urls": [ref], "num_images": n, "aspect_ratio": "16:9",
                                   "resolution": "2K", "output_format": "png"})
        rec["keys"] = []
        for i, im in enumerate(res["images"]):
            path = download(im["url"], os.path.join(sdir(style), "keys", f"{sid}_{i}.png"))
            rec["keys"].append({"url": im["url"], "path": path})
        save(style, st)
        print(sid, "keys", len(rec["keys"]), f"spent ${st['spent']:.2f}")
        if sid == "S1" and "pick" not in rec:
            print("-> look at gen/%s/sheets/S1.png, then: pick %s S1 <i>, and run keys again" % (style, style))
            sheet(style); return
    sheet(style)


def sheet(style):
    st = load(style)
    out = os.path.join(sdir(style), "sheets"); os.makedirs(out, exist_ok=True)
    for sid, rec in st["shots"].items():
        items = rec.get("keys", [])
        if not items:
            continue
        ins = sum([["-i", k["path"]] for k in items], [])
        lab = ";".join(f"[{i}]scale=640:-2,drawtext=text='{sid} {i}':x=10:y=10:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.6[v{i}]" for i in range(len(items)))
        grid = "".join(f"[v{i}]" for i in range(len(items)))
        fc = f"{lab};{grid}xstack=inputs={len(items)}:layout=" + "|".join(["0_0", "w0_0", "0_h0", "w0_h0"][:len(items)]) if len(items) > 1 else f"{lab}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-frames:v", "1",
                        os.path.join(out, f"{sid}.png")] if len(items) > 1 else
                       ["ffmpeg", "-v", "error", "-y", *ins, "-frames:v", "1", os.path.join(out, f"{sid}.png")], check=True)
    print("sheets in", out)


def pick(style, sid, i, field="pick"):
    st = load(style)
    targets = [s["id"] for s in SHOTS["shots"]] if sid == "auto" else [sid]
    for t in targets:
        rec = st["shots"].get(t, {})
        if field in rec and sid == "auto":
            continue
        rec[field] = 0 if sid == "auto" else int(i)
        st["shots"][t] = rec
    save(style, st)


def clips(style, takes=2):
    st = load(style)
    for shot in SHOTS["shots"]:
        sid = shot["id"]
        rec = st["shots"].get(sid, {})
        if "pick" not in rec:
            raise SystemExit(f"no keyframe picked for {sid}")
        rec.setdefault("takes", [])
        while len(rec["takes"]) < takes:
            dur = "5"
            spend(st, int(dur) * PRICE["video_s"], f"clip for {sid}")
            res = run(VIDEO_MODEL, {"start_image_url": rec["keys"][rec["pick"]]["url"], "prompt": prompt(style, shot, "move"),
                                    "negative_prompt": SHOTS["styles"][style]["negative"], "duration": dur,
                                    "generate_audio": False, "cfg_scale": 0.5})
            url = res["video"]["url"]
            i = len(rec["takes"])
            rec["takes"].append({"url": url, "path": download(url, os.path.join(sdir(style), "clips", f"{sid}_{i}.mp4"))})
            save(style, st)
            print(sid, "take", i, f"spent ${st['spent']:.2f}")


def frames(style):
    sys.path.insert(0, ROOT)
    import numpy as np, cv2, post
    st = load(style)
    for shot in SHOTS["shots"]:
        sid = shot["id"]
        rec = st["shots"][sid]
        take = rec["takes"][rec.get("take", 0)]["path"]
        n = int(round((shot["t"][1] - shot["t"][0]) * post.FPS)) + 1
        out = os.path.join(ROOT, "post", sid); os.makedirs(out, exist_ok=True)
        for f in os.listdir(out):
            os.remove(os.path.join(out, f))
        cap = cv2.VideoCapture(take)
        fps = cap.get(cv2.CAP_PROP_FPS) or 24
        skip = int(0.25 * fps)  # the first frames of a generated clip are often stiff
        for i in range(n):
            cap.set(cv2.CAP_PROP_POS_FRAMES, skip + int(i * fps / post.FPS))
            ok, fr = cap.read()
            if not ok:
                break
            fr = fr[..., ::-1].astype(np.float32) / 255
            h0, w0 = fr.shape[:2]
            th = w0 * post.H / post.W
            y0 = int((h0 - th) / 2)
            fr = cv2.resize(fr[y0:y0 + int(th)], (post.W, post.H), interpolation=cv2.INTER_CUBIC)
            lin = post.srgb_to_lin(fr)
            x = post.process_frame(lin, np.zeros((post.H, post.W), np.float32), None, i, None, fog_gain=0.0)
            post.write_png(os.path.join(out, f"p_{i:04d}.png"), x)
        print(sid, "frames", n)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "preflight":
        preflight()
    elif a[0] == "keys":
        keys(a[1], int(a[a.index("--n") + 1]) if "--n" in a else 4)
    elif a[0] == "sheet":
        sheet(a[1])
    elif a[0] == "pick":
        pick(a[1], a[2], a[3] if len(a) > 3 else 0)
    elif a[0] == "clips":
        clips(a[1], int(a[a.index("--takes") + 1]) if "--takes" in a else 2)
    elif a[0] == "take":
        pick(a[1], a[2], a[3] if len(a) > 3 else 0, field="take")
    elif a[0] == "frames":
        frames(a[1])
