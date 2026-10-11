"""Render a scene file to video: method E (graphics), cut to the episode's own narration.

    python3 -m gfx.render episodes/<ep>/scenes/<scene>.json            # lint + render + assemble
    python3 -m gfx.render <scene> --lint                                # only check the shot list
    python3 -m gfx.render <scene> --still 4@2.5                         # one frame of shot 4 → png
    python3 -m gfx.render <scene> --only 3,4 --workers 2 --preview      # 720p, some shots

Pipeline: scene JSON → resolve episode times (word anchors) and case references (@place,
@route) → per-shot render in headless Chromium (one deterministic frame per 1/25 s,
cached by content hash) → assemble with cuts/crossfades, grain and vignette → mux the
episode narration (untouched) over a quiet ambience bed → contact sheet + cue sheet.
"""
import argparse, hashlib, json, math, os, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from . import server as srv
from . import maptiles
from .timing import Transcript, parse_tc, fmt_tc, TIME_RE

GFX = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(GFX)
FPS = 25
W, H = 1920, 1080
TIME_KEYS = {"at", "until", "out", "words_until", "draw_until", "label_at", "sub_at", "who_at"}
TEMPLATES = {"map", "title", "quote", "facts", "timeline", "siteplan", "photo", "object", "card"}
GL_TEMPLATES = {"object"}  # need WebGL; everything else renders in software (much faster on CPU)
SOFT_ARGS = ["--disable-gpu", "--disable-gpu-compositing", "--font-render-hinting=none"]


# ------------------------------------------------------------------ loading / resolving
def load_scene(path):
    scene = json.load(open(path))
    ep_dir = os.path.dirname(os.path.dirname(os.path.abspath(path)))
    case = json.load(open(os.path.join(ep_dir, "case.json")))
    tx = Transcript(os.path.join(REPO, "audio", "transcript.json"))
    return scene, case, tx, ep_dir


def ref(case, s):
    """'@site' → [lon, lat]; '@route:id' → coordinates; '@area:id' → ring."""
    kind, _, key = s[1:].partition(":") if ":" in s else ("place", None, s[1:])
    if kind == "site":
        return case["site"][key]
    table = {"place": "places", "route": "routes", "area": "areas"}[kind]
    item = case[table][key]
    if kind == "place":
        return [item["lon"], item["lat"]]
    return item["coords"]


def resolve(obj, case, tx, t0, key=None):
    """Walk shot params: @refs → coordinates, times under TIME_KEYS → seconds after shot start."""
    if isinstance(obj, dict):
        if "word" in obj and "near" in obj and key in TIME_KEYS:
            return round(tx.resolve(obj) - t0, 3)
        return {k: resolve(v, case, tx, t0, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve(v, case, tx, t0, key) for v in obj]
    if isinstance(obj, str):
        if obj.startswith("@"):
            return ref(case, obj)
        if key in TIME_KEYS and TIME_RE.match(obj):
            return round(parse_tc(obj) - t0, 3)
    return obj


def trans(s):
    if not s or s == "cut":
        return ("cut", 0.0)
    kind, _, d = s.partition(":")
    return (kind, float(d or 0.6))


def build(scene, case, tx):
    a0, a1 = tx.resolve(scene["audio"]["from"]), tx.resolve(scene["audio"]["to"])
    shots = []
    for s in scene["shots"]:
        shots.append(dict(s, start=tx.resolve(s["at"])))
    shots.sort(key=lambda s: s["start"])
    for i, s in enumerate(shots):
        s["end"] = shots[i + 1]["start"] if i + 1 < len(shots) else a1
        s["dur"] = round(s["end"] - s["start"], 3)
        tin = trans(s.get("transition"))
        tout = trans(shots[i + 1].get("transition")) if i + 1 < len(shots) else ("cut", 0.0)
        s["pre"] = tin[1] / 2 if tin[0] == "fade" else 0.0
        s["post"] = tout[1] / 2 if tout[0] == "fade" else 0.0
        s["tin"], s["tout"] = tin, tout
        p = resolve(s.get("p", {}), case, tx, s["start"])
        if s["type"] == "quote" and p.get("speaker"):
            person = case["people"][p.pop("speaker")]
            p.setdefault("who", person["name"])
            p.setdefault("role", person["role"])
        if s["type"] == "quote" and "text" in p and "words" not in p:
            qa = tx.resolve(s["p"]["from"]) if "from" in s["p"] else s["start"] - 0.3
            qb = tx.resolve(s["p"]["to"]) if "to" in s["p"] else s["end"] + 0.3
            p["words"] = [[w, round(t - s["start"], 3)] for w, t in tx.align(p["text"], qa, qb)]
            p.pop("from", None); p.pop("to", None)
        lt = None
        if s.get("lt"):
            lt = resolve(s["lt"], case, tx, s["start"])
            if "who" in lt:
                lt = {**case["people"][lt.pop("who")], **lt}
                lt.pop("said", None)
        s["spec"] = {"type": s["type"], "p": p, "dur": s["dur"], "fps": FPS, "lt": lt, "tilekey": maptiles.tile_key(),
                     "fade_in": s.get("fade_in", 0), "fade_out": s.get("fade_out", 0),
                     "rain": s.get("rain", scene.get("rain", 0)), "credit": credit_for(s, p, case)}
    return a0, a1, shots


def credit_for(s, p, case):
    if s.get("credit") is not None:
        return s["credit"]
    if s["type"] == "map":
        c = "Kort: © OpenStreetMap-bidragydere, OpenMapTiles"
        if p.get("sat"):
            sat = os.environ.get("GFX_SAT", "esri")
            c += "  Luftfoto: " + ("SDFI" if sat.startswith("sdfi") else "Esri, Maxar, Earthstar Geographics")
        return c
    if s["type"] == "photo":
        return p.get("credit", "")
    return ""


# ------------------------------------------------------------------ lint
def lint(scene, case, tx, a0, a1, shots):
    errs, warns = [], []
    if not tx.words:
        errs.append("no transcript: run transcribe.py first")
    prev_end = a0
    for s in shots:
        sid = s["id"]
        if s["type"] not in TEMPLATES:
            errs.append(f"{sid}: unknown template {s['type']}")
        if s["start"] < a0 - 0.01 or s["start"] > a1:
            errs.append(f"{sid}: starts {fmt_tc(s['start'])} outside the scene audio")
        if s["dur"] < 1.0:
            errs.append(f"{sid}: only {s['dur']:.2f}s long")
        else:
            # a long graphic is fine while something changes in it; flag stretches where nothing does
            beats = sorted({0.0, s["dur"]} | {float(v) for k, v in walk(s["spec"]["p"])
                                              if k in TIME_KEYS and isinstance(v, (int, float)) and 0 < v < s["dur"]}
                           | {w[1] for w in s["spec"]["p"].get("words", []) if isinstance(w, list) and 0 < w[1] < s["dur"]})
            gap = max(b - a for a, b in zip(beats, beats[1:]))
            moving = s["type"] in ("map", "siteplan", "object") and len(s["spec"]["p"].get("cam", s["spec"]["p"].get("orbit", []))) > 1
            if gap > (12 if moving else 8):
                warns.append(f"{sid}: nothing new on screen for {gap:.1f}s of {s['dur']:.1f}s")
        if abs(s["start"] - prev_end) > 0.01 and s is shots[0] and s["start"] - a0 > 0.05:
            warns.append(f"{sid}: {s['start'] - a0:.2f}s of nothing before the first shot")
        prev_end = s["end"]
        # text density: Danish subtitle norm ≈ 15 characters per second on screen
        text = json.dumps(s["spec"]["p"], ensure_ascii=False)
        chars = sum(len(str(v)) for k, v in walk(s["spec"]["p"]) if k in ("h", "s", "text", "label", "sub", "lines", "heading"))
        if chars and chars / max(s["dur"], 0.1) > 18 and s["type"] != "quote":
            warns.append(f"{sid}: {chars} characters of text in {s['dur']:.1f}s — hard to read")
        for k, v in walk(s["spec"]["p"]):
            if k in TIME_KEYS and isinstance(v, (int, float)) and v > -0.99 and not (-s["pre"] - 0.5 <= v <= s["dur"] + s["post"] + 0.5):
                warns.append(f"{sid}: {k}={v:.2f}s lies outside the shot (0–{s['dur']:.2f}s)")
        if s["type"] == "quote" and s["spec"]["p"].get("words"):
            import difflib
            from .timing import norm
            ws = s["spec"]["p"]["words"]
            spoken = tx.words_between(s["start"] + min(w[1] for w in ws) - 1.0, s["end"] + 0.5)
            sm = difflib.SequenceMatcher(None, [norm(w[0]) for w in ws], [w["n"] for w in spoken], autojunk=False)
            ratio = sum(b.size for b in sm.get_matching_blocks()) / len(ws)
            if ratio < 0.7:
                warns.append(f"{sid}: only {ratio:.0%} of the quote matches what is said — check the wording or the window")
            if max(w[1] for w in ws) > s["dur"] + 0.3:
                warns.append(f"{sid}: the quote is still being spoken after the shot ends")
        for k, v in walk(s["spec"]["p"]):
            if k == "src" and isinstance(v, str) and not v.startswith("http"):
                if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(scene["_path"])), v)):
                    errs.append(f"{sid}: missing asset {v}")
    return errs, warns


def walk(o, k=None):
    if isinstance(o, dict):
        for kk, v in o.items():
            yield from walk(v, kk)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, k)
    else:
        yield k, o


# ------------------------------------------------------------------ per-shot render
def code_hash(kind):
    """Only the code a shot actually runs: editing one template must not re-render the others."""
    h = hashlib.sha1()
    files = ["runtime.js", "style.css", f"templates/{'title' if kind == 'card' else kind}.js"]
    if kind == "map":
        files.append("mapstyle.js")
    for f in files:
        h.update(open(os.path.join(GFX, "web", f), "rb").read())
    return h.hexdigest()[:10]


def shot_key(s, size):
    blob = json.dumps({"spec": s["spec"], "pre": s["pre"], "post": s["post"], "size": size, "code": code_hash(s["type"]),
                       "sat": os.environ.get("GFX_SAT", "esri")}, sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def _open(pw, kind, base, size):
    br = pw.chromium.launch(args=SOFT_ARGS if kind == "soft" else maptiles.GL_ARGS)
    pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=size[0] / W)
    pg.on("pageerror", lambda e: print("  [page error]", e, flush=True))
    pg.goto(base + "/web/index.html")
    pg.wait_for_function("window.GFX && Object.keys(GFX.templates).length >= (%d)" % (9 if kind == "gl" else 8), timeout=60000)
    return br, pg, pg.context.new_cdp_session(pg)


def _worker(jobs, base, size):
    import base64
    from playwright.sync_api import sync_playwright
    out = []
    with sync_playwright() as pw:
        pages = {}
        for job in jobs:
            kind = "gl" if job["spec"]["type"] in GL_TEMPLATES else "soft"
            if kind not in pages:
                pages[kind] = _open(pw, kind, base, size)
            br, pg, cdp = pages[kind]
            t_start = time.time()
            spec = dict(job["spec"], base=base)
            pg.evaluate("s => setupShot(s)", spec)
            if job.get("still") is not None:
                pg.evaluate("t => renderFrame(t)", job["still"])
                pg.screenshot(path=job["out"], type="png")
                out.append(job["out"])
                continue
            n = int(round((job["pre"] + job["dur"] + job["post"]) * FPS))
            tmp = job["out"] + ".part.mp4"
            enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-c:v", "mjpeg", "-r", str(FPS),
                                    "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-pix_fmt", "yuv420p",
                                    "-vf", f"scale={size[0]}:{size[1]}", tmp], stdin=subprocess.PIPE)
            for i in range(n):
                t = -job["pre"] + i / FPS
                pg.evaluate("t => renderFrame(t)", t)
                shot = cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 94, "optimizeForSpeed": True})
                enc.stdin.write(base64.b64decode(shot["data"]))
            enc.stdin.close()
            enc.wait()
            os.replace(tmp, job["out"])
            print(f"  shot {job['id']:>4} {job['spec']['type']:9s} {n:5d} frames {time.time() - t_start:6.1f}s", flush=True)
            out.append(job["out"])
        for br, _, _ in pages.values():
            br.close()
    return out


def prepare_maps(jobs, base):
    """Bake every map tile the map shots will touch, before any frame is rendered."""
    maps = [j for j in jobs if j["spec"]["type"] == "map"]
    if not maps:
        return
    from playwright.sync_api import sync_playwright
    need = set()
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=SOFT_ARGS)
        pg = br.new_page()
        pg.goto(base + "/web/index.html")
        pg.wait_for_function("window.GFX && typeof GFX.mapPlan === 'function'")
        for j in maps:
            plan = pg.evaluate("a => GFX.mapPlan(a[0], a[1])", [j["spec"]["p"], j["dur"] + j["post"]])
            need.update(plan["base"])
        br.close()
    maptiles.bake(need, base, maptiles.tile_key())


def render_shots(shots, ep_dir, size, workers, only=None, force=False):
    cache = os.path.join(REPO, "render", "shots")
    os.makedirs(cache, exist_ok=True)
    jobs = []
    for s in shots:
        s["file"] = os.path.join(cache, f"{shot_key(s, size)}_{size[1]}.mp4")
        if only and s["id"] not in only:
            continue
        if os.path.exists(s["file"]) and not force:
            continue
        jobs.append({"id": s["id"], "spec": s["spec"], "pre": s["pre"], "dur": s["dur"], "post": s["post"],
                     "out": s["file"], "cost": s["dur"] * (4 if s["type"] == "object" else 1.5 if s["type"] == "map" else 1)})
    if not jobs:
        print("all shots cached")
        return
    print(f"rendering {len(jobs)} shot(s) on {workers} worker(s)")
    server, base = srv.start(ep_dir)
    prepare_maps(jobs, base)
    jobs.sort(key=lambda j: -j["cost"])
    buckets = [[] for _ in range(max(1, min(workers, len(jobs))))]
    loads = [0.0] * len(buckets)
    for j in jobs:
        i = loads.index(min(loads))
        buckets[i].append(j)
        loads[i] += j["cost"]
    if len(buckets) == 1:
        _worker(buckets[0], base, size)
    else:
        with ProcessPoolExecutor(len(buckets)) as ex:
            list(ex.map(_worker, buckets, [base] * len(buckets), [size] * len(buckets)))
    server.shutdown()


# ------------------------------------------------------------------ assembly
class Reader:
    def __init__(self, path, size):
        self.size = size
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE)
        self.idx, self.last = -1, None

    def get(self, i):
        n = self.size[0] * self.size[1] * 3
        while self.idx < i:
            buf = self.p.stdout.read(n)
            if len(buf) < n:
                break
            self.last = np.frombuffer(buf, np.uint8).reshape(self.size[1], self.size[0], 3)
            self.idx += 1
        return self.last

    def close(self):
        self.p.kill()


def assemble(scene, a0, a1, shots, out, size, ep_dir, web=True, graded=True):
    """Cut the shots on the episode clock → clean picture; then mux narration + bed into
    the deliverable (with grain and vignette) and a small web version for review."""
    n = int(round((a1 - a0) * FPS))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    clean = out.replace(".mp4", "_clean.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                            "-pix_fmt", "yuv420p", clean], stdin=subprocess.PIPE)
    readers = {}
    black = np.zeros((size[1], size[0], 3), np.uint8)
    by_id = {s["id"]: s for s in shots}

    def frame_of(s, T):
        r = readers.get(s["id"])
        if r is None:
            r = readers[s["id"]] = Reader(s["file"], size)
        f = r.get(max(0, int(round((T - (s["start"] - s["pre"])) * FPS))))
        return black if f is None else f

    for k in range(n):
        T = a0 + k / FPS + 1e-6
        cur = next((s for s in shots if s["start"] <= T < s["end"]), shots[-1] if T >= shots[-1]["start"] else None)
        if cur is None:
            enc.stdin.write(black.tobytes())
            continue
        i = shots.index(cur)
        base = frame_of(cur, T)
        img = None
        if cur["tout"][0] == "fade" and i + 1 < len(shots) and T >= cur["end"] - cur["tout"][1] / 2:
            a = (T - (cur["end"] - cur["tout"][1] / 2)) / cur["tout"][1]
            img = base.astype(np.float32) * (1 - a) + frame_of(shots[i + 1], T).astype(np.float32) * a
        elif cur["tin"][0] == "fade" and i > 0 and T < cur["start"] + cur["tin"][1] / 2:
            a = 0.5 + (T - cur["start"]) / cur["tin"][1]
            img = frame_of(shots[i - 1], T).astype(np.float32) * (1 - a) + base.astype(np.float32) * a
        if cur["tin"][0] == "dip" and T < cur["start"] + cur["tin"][1] / 2:
            img = (base.astype(np.float32) if img is None else img) * ((T - cur["start"]) / (cur["tin"][1] / 2))
        if cur["tout"][0] == "dip" and T > cur["end"] - cur["tout"][1] / 2:
            img = (base.astype(np.float32) if img is None else img) * ((cur["end"] - T) / (cur["tout"][1] / 2))
        enc.stdin.write(base.tobytes() if img is None else np.clip(img, 0, 255).astype(np.uint8).tobytes())
        for sid in [x for x in readers if T > by_id[x]["end"] + by_id[x]["post"] + 0.1]:
            readers.pop(sid).close()
    enc.stdin.close()
    enc.wait()
    for r in readers.values():
        r.close()
    # audio: the episode's narration, untouched, over a quiet ambience bed
    ep_audio = os.path.join(REPO, "audio", "episode.mp3")
    bed = scene.get("bed", "rain")
    d = a1 - a0
    if bed == "rain":
        bed_src = ["-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.6:seed=7:duration={d:.3f},"
                   "highpass=f=350,lowpass=f=5200,aformat=channel_layouts=stereo"]
        mix = (f"[1:a]volume={scene.get('bed_db', -31)}dB,afade=t=in:d=0.8,afade=t=out:st={d - 0.8:.3f}:d=0.8[b];"
               f"[0:a]afade=t=in:d=0.15,afade=t=out:st={d - 0.3:.3f}:d=0.3[n];[n][b]amix=inputs=2:normalize=0[a]")
    else:
        bed_src = []
        mix = f"[0:a]afade=t=in:d=0.15,afade=t=out:st={d - 0.3:.3f}:d=0.3[a]"
    vin = 2 if bed_src else 1
    audio_in = ["-ss", f"{a0:.3f}", "-t", f"{d:.3f}", "-i", ep_audio, *bed_src, "-i", clean]
    # deliverable: film grain (luma, temporal) + soft vignette. Grain is expensive to encode; that is the point.
    if graded:
      subprocess.run(["ffmpeg", "-v", "error", "-y", *audio_in, "-filter_complex",
                    mix + f";[{vin}:v]noise=c0s=5:c0f=t,vignette=angle=0.42[v]", "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    if web:  # small review copy: no grain, 720p
        subprocess.run(["ffmpeg", "-v", "error", "-y", *audio_in, "-filter_complex",
                        mix + f";[{vin}:v]scale=1280:720,vignette=angle=0.42[v]", "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "25", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                        "-movflags", "+faststart", "-shortest", out.replace(".mp4", "_web.mp4")], check=True)


def contact_sheet(scene, shots, out_jpg, size):
    from PIL import Image, ImageDraw, ImageFont
    thumbs = []
    for s in shots:
        t = s["pre"] + s["dur"] * 0.6
        tmp = out_jpg + f".{s['id']}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", s["file"], "-frames:v", "1",
                        "-vf", "scale=480:270", tmp], check=True)
        thumbs.append((s, Image.open(tmp).convert("RGB")))
        os.remove(tmp)
    cols = 4
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 490 + 10, rows * 316 + 10), (14, 20, 24))
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype(os.path.join(GFX, "web", "fonts", "Archivo[wdth,wght].ttf"), 18)
    except Exception:
        font = ImageFont.load_default()
    for k, (s, im) in enumerate(thumbs):
        x, y = 10 + (k % cols) * 490, 10 + (k // cols) * 316
        sheet.paste(im, (x, y))
        dr.text((x, y + 276), f"{s['id']}  {fmt_tc(s['start'])}  {s['type']}  {s['dur']:.1f}s", fill=(200, 200, 190), font=font)
    sheet.save(out_jpg, quality=88)


def cue_sheet(scene, shots, out_json):
    rows = [{"shot": s["id"], "from": fmt_tc(s["start"]), "to": fmt_tc(s["end"]), "template": s["type"],
             "generated_by_ai": False, "sources": s["spec"]["credit"], "note": s.get("note", "")} for s in shots]
    json.dump({"scene": scene["id"], "method": "E (graphics, rendered from code)", "shots": rows},
              open(out_json, "w"), ensure_ascii=False, indent=1)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--lint", action="store_true")
    ap.add_argument("--still")
    ap.add_argument("--only")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument("--preview", action="store_true", help="1280x720")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    scene, case, tx, ep_dir = load_scene(args.scene)
    scene["_path"] = os.path.abspath(args.scene)
    a0, a1, shots = build(scene, case, tx)
    errs, warns = lint(scene, case, tx, a0, a1, shots)
    print(f"scene {scene['id']}: {fmt_tc(a0)}–{fmt_tc(a1)} ({a1 - a0:.1f}s), {len(shots)} shots, "
          f"avg {(a1 - a0) / max(1, len(shots)):.1f}s")
    for w in warns:
        print("  warn:", w)
    for e in errs:
        print("  ERROR:", e)
    if errs:
        sys.exit(1)
    if args.lint:
        for s in shots:
            print(f"  {s['id']:>4} {fmt_tc(s['start'])} {s['dur']:5.2f}s {s['type']:9s} "
                  f"| {tx.text_between(s['start'], s['end'])[:90]}")
        return
    size = (1280, 720) if args.preview else (W, H)
    if args.still:
        jobs = []
        for item in args.still.split(","):
            sid, _, t = item.partition("@")
            s = next(x for x in shots if x["id"] == sid)
            out = os.path.join(REPO, "render", "stills", f"{scene['id']}_{sid}_{t}.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            jobs.append({"id": sid, "spec": s["spec"], "pre": 0, "dur": s["dur"], "post": 0, "out": out,
                         "still": float(t or s["dur"] / 2)})
        server, base = srv.start(ep_dir)
        prepare_maps(jobs, base)
        for o in _worker(jobs, base, size):
            print(o)
        server.shutdown()
        return
    only = set(args.only.split(",")) if args.only else None
    render_shots(shots, ep_dir, size, args.workers, only, args.force)
    if only:
        return
    tag = "_720" if args.preview else ""
    out = os.path.join(REPO, "out", "gfx", f"{scene['id']}{tag}.mp4")
    t = time.time()
    assemble(scene, a0, a1, shots, out, size, ep_dir, graded=not args.preview)
    contact_sheet(scene, shots, out.replace(".mp4", "_sheet.jpg"), size)
    cue_sheet(scene, shots, out.replace(".mp4", "_cues.json"))
    print(f"assembled {out} in {time.time() - t:.0f}s")


if __name__ == "__main__":
    main()
