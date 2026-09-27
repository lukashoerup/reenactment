"""Animate section-1 keyframes on Google Cloud (Veo 3.1 Lite), then let the judge pick/approve takes.
python3 sec1/clips.py gen [ids...]     # generate missing takes (1 take for pinned shots, 2 otherwise)
python3 sec1/clips.py pick [ids...]    # judge: choose between takes / pass-fail single takes -> sec1/picks.json
Spend cap for the section: CAP_USD (default 60, list price) counted from spend.log entries tagged sec1.
"""
import base64, io, json, os, subprocess, sys, time, concurrent.futures as cf
import requests
from PIL import Image
from google.oauth2 import service_account
from google.auth.transport.requests import Request

KEY = os.environ["VERTEX_KEY_FILE"]; P = json.load(open(KEY))["project_id"]
LOC = "us-central1"; VEO = os.environ.get("VEO", "veo-3.1-lite-generate-001"); VEO_USD = 0.05
JUDGE = os.environ.get("JUDGE", "gemini-3.1-pro-preview")
CAP = float(os.environ.get("CAP_USD", "60"))
data = json.load(open("sec1/shots.json")); SH = {s["id"]: s for s in data["shots"]}
os.makedirs("sec1/clips", exist_ok=True)
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
        if d.get("section") == "sec1" or str(d.get("shot", "")).startswith(("s", "c")) and d.get("backend") == "vertex":
            tot += d.get("usd_est", 0) or 0
    return tot

def log(e):
    with open("spend.log", "a") as f: f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "backend": "vertex", "section": "sec1", **e}) + "\n")

def img(path):
    im = Image.open(path).convert("RGB").resize((1280, 720), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "PNG")
    return {"bytesBase64Encoded": base64.b64encode(b.getvalue()).decode(), "mimeType": "image/png"}

def gen(s, n=None, extra=""):
    n = n or (1 if s["pin"] else 2)
    if spent() + n * s["dur"] * VEO_USD > CAP:
        print(s["id"], "skipped: cap"); return []
    base = f"https://{LOC}-aiplatform.googleapis.com/v1/projects/{P}/locations/{LOC}/publishers/google/models/{VEO}"
    inst = {"prompt": s["motion_prompt"] + (" " + extra if extra else ""), "image": img(f"sec1/kf/{s['id']}.png")}
    if s["pin"]: inst["lastFrame"] = inst["image"]
    params = {"sampleCount": n, "durationSeconds": s["dur"], "aspectRatio": "16:9", "resolution": "720p",
              "generateAudio": True, "personGeneration": "allow_adult", "negativePrompt": s["negative"]}
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
    k0 = len([f for f in os.listdir("sec1/clips") if f.startswith(s["id"] + "_t")])
    outs = []
    for i, v in enumerate(vids):
        if "bytesBase64Encoded" not in v: continue
        f = f"sec1/clips/{s['id']}_t{k0 + i + 1}.mp4"; open(f, "wb").write(base64.b64decode(v["bytesBase64Encoded"])); outs.append(f)
    log({"kind": "video", "model": VEO, "shot": s["id"], "n": len(outs), "dur": s["dur"], "usd_est": len(outs) * s["dur"] * VEO_USD,
         "filtered": resp.get("raiMediaFilteredCount", 0), "reasons": resp.get("raiMediaFilteredReasons", [])[:2]})
    print(s["id"], "->", outs, "filtered", resp.get("raiMediaFilteredCount", 0), flush=True)
    return outs

def used_window(s, clip):
    slot = s["end"] - s["start"]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip], capture_output=True, text=True).stdout)
    return 0.0, min(slot, dur)

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
A take FAILS if: anything moves without a visible cause (objects flying in, logs thrown, things appearing/disappearing);
a person appears who is not asked for; any face; any child; any body or body part of a victim; the drawn style turns
photographic, 3D or cartoon; morphing/melting; readable text; the motion contradicts the intended shot.
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

def takes_of(sid): return sorted(f"sec1/clips/{f}" for f in os.listdir("sec1/clips") if f.startswith(sid + "_t") and f.endswith(".mp4") and "_use" not in f)

def do_gen(s):
    if not os.path.exists(f"sec1/kf/{s['id']}.png") or takes_of(s["id"]): return
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
    todo = [s for s in data["shots"] if s["kind"] == "new" and s.get("motion_prompt") and (not ids or s["id"] in ids)]
    with cf.ThreadPoolExecutor(int(os.environ.get('PAR','2'))) as ex:
        if mode == "gen":
            list(ex.map(do_gen, todo))
        else:
            PF = os.environ.get("PICKS", "sec1/picks.json"); picks = json.load(open(PF)) if os.path.exists(PF) else {}
            for sid, v in ex.map(do_pick, [s for s in todo if s["id"] not in picks]):
                picks[sid] = v; print(sid, "pick", v.get("pick"), "pass", v.get("pass"), v.get("problems"), flush=True)
                json.dump(picks, open(PF, "w"), ensure_ascii=False, indent=1)
    print(f"section spend so far ≈ ${spent():.2f} (list)")
