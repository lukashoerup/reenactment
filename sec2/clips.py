"""Section 2: only the few 'ambient' shots are animated (Veo 3.1 Lite on Google Cloud): first frame = last frame,
6 s, 2 takes, audio off (sound is built in post), then the judge picks. The edit plays them at ~0.5x ("on twos").
python3 sec2/clips.py gen [ids...]     # generate missing takes
python3 sec2/clips.py pick [ids...]    # judge: choose / fail -> one more round with the judge's fix -> sec2/picks.json
Spend cap for the section: CAP_USD (default 15, list price) counted from spend.log entries tagged sec2.
"""
import base64, io, json, os, subprocess, sys, time, concurrent.futures as cf
import requests
from PIL import Image
from google.oauth2 import service_account
from google.auth.transport.requests import Request

KEY = os.environ["VERTEX_KEY_FILE"]; P = json.load(open(KEY))["project_id"]
LOC = "us-central1"; VEO = os.environ.get("VEO", "veo-3.1-lite-generate-001"); VEO_USD = 0.05
JUDGE = os.environ.get("JUDGE", "gemini-3.1-pro-preview")
CAP = float(os.environ.get("CAP_USD", "15"))
data = json.load(open("sec2/shots.json")); SH = {s["id"]: s for s in data["shots"]}
os.makedirs("sec2/takes", exist_ok=True)
_tok = {"t": 0, "v": None}

def token():
    if time.time() - _tok["t"] > 1800:
        c = service_account.Credentials.from_service_account_file(KEY, scopes=["https://www.googleapis.com/auth/cloud-platform"])
        c.refresh(Request()); _tok.update(t=time.time(), v=c.token)
    return _tok["v"]

def H(): return {"Authorization": f"Bearer {token()}", "Content-Type": "application/json"}

def spent():
    tot = 0.0
    for l in open("spend.log"):
        try: d = json.loads(l)
        except Exception: continue
        if d.get("section") == "sec2":
            tot += d.get("usd_est", 0) or 0
    return tot

def log(e):
    with open("spend.log", "a") as f: f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "backend": "vertex", "section": "sec2", **e}) + "\n")

def img(path):
    im = Image.open(path).convert("RGB").resize((1280, 720), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "PNG")
    return {"bytesBase64Encoded": base64.b64encode(b.getvalue()).decode(), "mimeType": "image/png"}

def gen(s, n=None, extra=""):
    n = n or 2; s = dict(s, dur=6)
    if spent() + n * s["dur"] * VEO_USD > CAP:
        print(s["id"], "skipped: cap"); return []
    base = f"https://{LOC}-aiplatform.googleapis.com/v1/projects/{P}/locations/{LOC}/publishers/google/models/{VEO}"
    inst = {"prompt": s["motion_prompt"] + (" " + extra if extra else ""), "image": img(f"sec2/kf/{s['id']}.png")}
    inst["lastFrame"] = inst["image"]
    params = {"sampleCount": n, "durationSeconds": s["dur"], "aspectRatio": "16:9", "resolution": "720p",
              "generateAudio": False, "personGeneration": "allow_adult", "negativePrompt": s["negative"]}
    for attempt in range(4):
        r = requests.post(f"{base}:predictLongRunning", headers=H(), json={"instances": [inst], "parameters": params}, timeout=120)
        if r.status_code == 400 and "negative" in r.text.lower() and "negativePrompt" in params:
            params.pop("negativePrompt"); continue
        if r.status_code in (429, 500, 503): time.sleep(20 * (attempt + 1)); continue
        break
    if not r.ok: print(s["id"], "submit", r.status_code, r.text[:300]); return []
    op = r.json()["name"]
    while True:
        time.sleep(10)
        p = requests.post(f"{base}:fetchPredictOperation", headers=H(), json={"operationName": op}, timeout=120).json()
        if p.get("done"): break
    if "error" in p: print(s["id"], "error", json.dumps(p["error"])[:300]); return []
    resp = p.get("response", {}); vids = resp.get("videos", [])
    k0 = len(takes_of(s["id"]))   # count real takes only (section 1 also counted the judge's *_use.mp4 cuts)
    outs = []
    for i, v in enumerate(vids):
        if "bytesBase64Encoded" not in v: continue
        f = f"sec2/takes/{s['id']}_t{k0 + i + 1}.mp4"; open(f, "wb").write(base64.b64decode(v["bytesBase64Encoded"])); outs.append(f)
    log({"kind": "video", "model": VEO, "shot": s["id"], "n": len(outs), "dur": s["dur"], "usd_est": len(outs) * s["dur"] * VEO_USD,
         "filtered": resp.get("raiMediaFilteredCount", 0), "reasons": resp.get("raiMediaFilteredReasons", [])[:2]})
    print(s["id"], "->", outs, "filtered", resp.get("raiMediaFilteredCount", 0), flush=True)
    return outs

def used_window(s, clip):   # the whole 6 s take is used (played at ~0.5x)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip], capture_output=True, text=True).stdout)
    return 0.0, dur

def cut(clip, a, b):
    out = clip.replace(".mp4", "_use.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-t", f"{b-a}", "-i", clip, "-vf", "scale=854:480", "-c:v", "libx264", "-crf", "24", "-c:a", "aac", out], check=True)
    return out

def judge(s, takes):
    parts = []
    for i, t in enumerate(takes):
        a, b = used_window(s, t)
        parts += [{"text": f"TAKE {i+1}:"}, {"inlineData": {"mimeType": "video/mp4", "data": base64.b64encode(open(cut(t, a, b), "rb").read()).decode()}, "videoMetadata": {"fps": 8}}]
    prompt = f"""You are the picture editor of a Danish true-crime documentary drawn in charcoal and ink. Above are {len(takes)} take(s)
of ONE shot, exactly the part that will be used. Intended shot: {s['image']} Intended motion: {s['motion']}
Narration over it: "{s['line']}"
The take will be played at half speed, so it must be calm. A take FAILS if: anything other than smoke, steam, rain,
running water or a steady flame moves; any object moves, appears, disappears, changes shape or floats; the camera moves;
a person, hand or animal appears; any body or body part of a victim, or anything that could be read as one; the drawn
style turns photographic, 3D or cartoon; morphing or melting; readable text; sudden flashes; rain that blinks on and off.
Return JSON only: {{"best": 1-based index of the best take or 0 if all fail, "pass": bool (best take is usable),
"problems": [short strings about the best take], "fix": "one sentence to add to the motion prompt if it failed"}}"""
    for attempt in range(8):
        r = requests.post(f"https://aiplatform.googleapis.com/v1/projects/{P}/locations/global/publishers/google/models/{JUDGE}:generateContent",
                          headers=H(), json={"contents": [{"role": "user", "parts": parts + [{"text": prompt}]}],
                                             "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}}, timeout=300)
        if r.status_code in (429, 500, 503): time.sleep(min(30 * (attempt + 1), 120)); continue
        break
    if not r.ok: return {"best": 1, "pass": None, "problems": ["UNJUDGED: " + r.text[:80]], "fix": ""}
    log({"kind": "judge-video", "model": JUDGE, "shot": s["id"], "usd_est": 0.05})
    v = json.loads("".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"]))
    return v[0] if isinstance(v, list) else v

def takes_of(sid): return sorted(f"sec2/takes/{f}" for f in os.listdir("sec2/takes") if f.startswith(sid + "_t") and f.endswith(".mp4") and "_use" not in f)

def do_gen(s):
    if not os.path.exists(f"sec2/kf/{s['id']}.png") or takes_of(s["id"]): return
    gen(s)

def do_pick(s):
    tk = takes_of(s["id"])
    if not tk: return s["id"], {"pick": None, "note": "no takes"}
    v = judge(s, tk)
    if v.get("pass") is False and spent() < CAP:
        new = gen(s, n=2, extra=v.get("fix", ""))
        if new:
            tk2 = takes_of(s["id"]); v2 = judge(s, tk2)
            v2["round"] = 2; v2["first"] = v
            return s["id"], {"pick": tk2[v2["best"] - 1] if v2.get("best") else tk2[-1], **v2}
    return s["id"], {"pick": tk[v["best"] - 1] if v.get("best") else tk[0], **v}

if __name__ == "__main__":
    mode, ids = sys.argv[1], sys.argv[2:]
    todo = [s for s in data["shots"] if s["kind"] == "ambient" and (not ids or s["id"] in ids)]
    with cf.ThreadPoolExecutor(int(os.environ.get('PAR','2'))) as ex:
        if mode == "gen":
            list(ex.map(do_gen, todo))
        else:
            PF = os.environ.get("PICKS", "sec2/picks.json"); picks = json.load(open(PF)) if os.path.exists(PF) else {}
            for sid, v in ex.map(do_pick, [s for s in todo if s["id"] not in picks]):
                picks[sid] = v; print(sid, "pick", v.get("pick"), "pass", v.get("pass"), v.get("problems"), flush=True)
                json.dump(picks, open(PF, "w"), ensure_ascii=False, indent=1)
    print(f"section spend so far ≈ ${spent():.2f} (list)")
