"""Drawn keyframes for section 1 on Google Cloud (gemini-3-pro-image), with a keyframe gate
(gemini-3.1-pro-preview looks at each image against the rules; one automatic redo with its notes).
python3 sec1/keys.py [ids...]      # default: all new shots without a keyframe yet
"""
import base64, json, os, sys, time, concurrent.futures as cf
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

KEY = os.environ["VERTEX_KEY_FILE"]; P = json.load(open(KEY))["project_id"]
URL = "https://aiplatform.googleapis.com/v1/projects/{p}/locations/global/publishers/google/models/{m}:generateContent"
IMG_MODEL, JUDGE = os.environ.get("IMG_MODEL", "gemini-3-pro-image"), "gemini-3.1-pro-preview"
STYLE_REFS = os.environ.get("STYLE_REFS", "kfC/S2.png,kfC/S4.png").split(",")
OUT = "sec1/kf"; os.makedirs(OUT, exist_ok=True)
data = json.load(open("sec1/shots.json")); SH = {s["id"]: s for s in data["shots"]}
_tok = {"t": 0, "v": None}

def token():
    if time.time() - _tok["t"] > 1800:
        c = service_account.Credentials.from_service_account_file(KEY, scopes=["https://www.googleapis.com/auth/cloud-platform"])
        c.refresh(Request()); _tok.update(t=time.time(), v=c.token)
    return _tok["v"]

def part(path, mime="image/png"):
    return {"inlineData": {"mimeType": mime, "data": base64.b64encode(open(path, "rb").read()).decode()}}

def log(e):
    with open("spend.log", "a") as f: f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "backend": "vertex", **e}) + "\n")

def call(model, parts, cfg):
    for attempt in range(8):
        r = requests.post(URL.format(p=P, m=model), headers={"Authorization": f"Bearer {token()}"},
                          json={"contents": [{"role": "user", "parts": parts}], "generationConfig": cfg}, timeout=300)
        if r.status_code in (429, 500, 503): time.sleep(min(30 * (attempt + 1), 120)); continue
        return r
    return r

def draw(s, extra=""):
    refs = [part(p) for p in STYLE_REFS]
    txt = ("Match the drawing technique, paper, line quality and palette of the first two reference images exactly. ")
    if s.get("ref"):
        refs.append(part(f"{OUT}/{s['ref']}.png"))
        txt += "The last reference image shows the same place or objects: keep them consistent (same place, same objects, same light), but compose this new shot as described. "
    txt += s["image_prompt"] + (" Avoid: " + extra if extra else "")
    r = call(IMG_MODEL, refs + [{"text": txt}], {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9", "imageSize": "2K"}})
    ok = False
    if r.ok:
        for c in r.json().get("candidates", []):
            for p in c.get("content", {}).get("parts", []):
                d = p.get("inlineData")
                if d: open(f"{OUT}/{s['id']}.png", "wb").write(base64.b64decode(d["data"])); ok = True
    log({"kind": "image", "model": IMG_MODEL, "shot": s["id"], "ok": ok, "usd_est": (0.134 if "pro" in IMG_MODEL else 0.10) if ok else 0})
    if not ok: print(s["id"], "draw failed", r.status_code, r.text[:300])
    return ok

def gate(s):
    prompt = f"""You check one keyframe for a Danish true-crime documentary re-enactment drawn in charcoal and ink.
Intended shot: {s['image']}
Narration over it: "{s['line']}"
FAIL if any of these is true: a visible face or facial features (people must be seen from behind, in silhouette or as hands);
any person who is not asked for in the intended shot; any child; any body, body part, blood or injury of a victim;
any readable text, letters, numbers or logo; the image looks like a photograph, 3D render, anime or comic instead of a
charcoal/ink drawing on grey paper; anatomical errors (extra fingers, merged hands); the image does not show the intended shot.
Return JSON only: {{"pass": bool, "problems": [short strings], "avoid": "one short sentence of things to avoid when redrawing"}}"""
    r = call(JUDGE, [part(f"{OUT}/{s['id']}.png"), {"text": prompt}], {"responseMimeType": "application/json", "temperature": 0.1})
    log({"kind": "judge-image", "model": JUDGE, "shot": s["id"], "ok": r.ok, "usd_est": 0.02})
    if not r.ok: return {"pass": True, "problems": ["judge unavailable: " + r.text[:120]], "avoid": ""}
    v = json.loads("".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"]))
    return v[0] if isinstance(v, list) else v

def run(s):
    res = {"id": s["id"], "tries": []}
    extra = ""
    for t in range(2):
        if not draw(s, extra): res["tries"].append({"draw": "failed"}); continue
        g = gate(s); res["tries"].append(g)
        if g.get("pass"): break
        extra = g.get("avoid", "") + " " + "; ".join(g.get("problems", []))
        os.replace(f"{OUT}/{s['id']}.png", f"{OUT}/{s['id']}_rejected{t}.png")
    res["final"] = os.path.exists(f"{OUT}/{s['id']}.png")
    if not res["final"] and os.path.exists(f"{OUT}/{s['id']}_rejected1.png"):
        os.replace(f"{OUT}/{s['id']}_rejected1.png", f"{OUT}/{s['id']}.png"); res["final"] = "kept-despite-gate"
    print(s["id"], json.dumps(res["tries"][-1] if res["tries"] else {}, ensure_ascii=False)[:220], flush=True)
    return res

todo = [s for s in data["shots"] if s["kind"] == "new" and s["image"] not in ("", "BLACK")]
if len(sys.argv) > 1: todo = [s for s in todo if s["id"] in sys.argv[1:]]
todo = [s for s in todo if not os.path.exists(f"{OUT}/{s['id']}.png")]
done = {s["id"] for s in data["shots"] if os.path.exists(f"{OUT}/{s['id']}.png")}
report = json.load(open("sec1/keys_report.json")) if os.path.exists("sec1/keys_report.json") else {}
while todo:
    wave = [s for s in todo if not s.get("ref") or s["ref"] in done]
    if not wave: print("unresolved refs:", [s["id"] for s in todo]); break
    with cf.ThreadPoolExecutor(int(os.environ.get('KEYS_PAR','2'))) as ex:
        for res in ex.map(run, wave):
            report[res["id"]] = res
            if res["final"]: done.add(res["id"])
    failed = [s["id"] for s in wave if s["id"] not in done]
    if failed: print("failed this wave (will not retry now):", failed, flush=True)
    todo = [s for s in todo if s["id"] not in done and s not in wave]
json.dump(report, open("sec1/keys_report.json", "w"), ensure_ascii=False, indent=1)
print("keyframes:", len(done))
