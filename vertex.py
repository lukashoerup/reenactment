"""Google Cloud (Vertex AI / Agent Platform) backend: service-account key -> access token -> Veo, images, judge.
Key file path comes from $VERTEX_KEY_FILE (never printed, never committed). Project id is read from the key.

python3 vertex.py check                                   # token + one tiny text call (≈ $0.0001)
python3 vertex.py video OUT.mp4 FIRST.png "motion prompt" [--last LAST.png] [--dur 4] [--model veo-3.1-fast-generate-001]
                        [--n 1] [--no-audio] [--neg "thrown object, stick, hand, person entering frame"] [--no-enhance]
"""
import argparse, base64, io, json, os, sys, time
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

KEY = os.environ.get("VERTEX_KEY_FILE", "")
LOC = os.environ.get("VERTEX_LOCATION", "us-central1")
PRICE_S = {"veo-3.1-generate-001": 0.20, "veo-3.1-fast-generate-001": 0.10, "veo-3.1-lite-generate-001": 0.05}

def session():
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(Request())
    project = json.load(open(KEY))["project_id"]
    s = requests.Session(); s.headers.update({"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"})
    return s, project

def log(entry):
    with open("spend.log", "a") as f:
        f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "backend": "vertex", **entry}) + "\n")

def img_b64(path):
    from PIL import Image
    im = Image.open(path).convert("RGB").resize((1280, 720), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "PNG")
    return {"bytesBase64Encoded": base64.b64encode(buf.getvalue()).decode(), "mimeType": "image/png"}

def check():
    s, project = session()
    print("token ok, project:", project)
    url = f"https://{LOC}-aiplatform.googleapis.com/v1/projects/{project}/locations/{LOC}/publishers/google/models/gemini-2.5-flash:generateContent"
    r = s.post(url, json={"contents": [{"role": "user", "parts": [{"text": "Reply with the single word OK."}]}]}, timeout=60)
    print("text call:", r.status_code, (r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "") if r.ok else r.text[:400]))

def video(a):
    s, project = session()
    base = f"https://{LOC}-aiplatform.googleapis.com/v1/projects/{project}/locations/{LOC}/publishers/google/models/{a.model}"
    inst = {"prompt": a.prompt, "image": img_b64(a.first)}
    if a.last: inst["lastFrame"] = img_b64(a.last)
    params = {"sampleCount": a.n, "durationSeconds": a.dur, "aspectRatio": "16:9", "resolution": "720p",
              "generateAudio": not a.no_audio, "personGeneration": "allow_adult"}
    if a.neg: params["negativePrompt"] = a.neg
    if a.no_enhance: params["enhancePrompt"] = False
    t0 = time.time()
    r = s.post(f"{base}:predictLongRunning", json={"instances": [inst], "parameters": params}, timeout=120)
    if not r.ok:
        print("SUBMIT", r.status_code, r.text[:800]); sys.exit(1)
    op = r.json()["name"]
    while True:
        time.sleep(10)
        p = s.post(f"{base}:fetchPredictOperation", json={"operationName": op}, timeout=120).json()
        if p.get("done"): break
    if "error" in p:
        print("ERROR", json.dumps(p["error"])[:800]); log({"kind": "video", "model": a.model, "ok": False}); sys.exit(1)
    resp = p.get("response", {})
    vids = resp.get("videos", [])
    if not vids:
        print("NO VIDEO", json.dumps(resp)[:800]); log({"kind": "video", "model": a.model, "ok": False}); sys.exit(1)
    outs = []
    for i, v in enumerate(vids):
        out = a.out if len(vids) == 1 else a.out.replace(".mp4", f"_{i+1}.mp4")
        if "bytesBase64Encoded" in v:
            open(out, "wb").write(base64.b64decode(v["bytesBase64Encoded"]))
        else:
            print("video stored at", v.get("gcsUri"), "- set storageUri or download it"); continue
        outs.append(out)
    usd = len(outs) * a.dur * PRICE_S.get(a.model, 0.4)
    log({"kind": "video", "model": a.model, "dur": a.dur, "n": len(outs), "audio": not a.no_audio, "out": outs, "ok": bool(outs), "usd_est": usd})
    print("saved", outs, f"{time.time()-t0:.0f}s", f"~${usd:.2f} (list, before audio-off discount)",
          "filtered:", resp.get("raiMediaFilteredCount", 0))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    v = sub.add_parser("video"); v.add_argument("out"); v.add_argument("first"); v.add_argument("prompt")
    v.add_argument("--last"); v.add_argument("--dur", type=int, default=4); v.add_argument("--n", type=int, default=1)
    v.add_argument("--model", default="veo-3.1-fast-generate-001"); v.add_argument("--no-audio", action="store_true")
    v.add_argument("--neg", default=""); v.add_argument("--no-enhance", action="store_true")
    a = ap.parse_args()
    if not KEY or not os.path.exists(KEY): sys.exit("set VERTEX_KEY_FILE to the service-account key path")
    check() if a.cmd == "check" else video(a)
