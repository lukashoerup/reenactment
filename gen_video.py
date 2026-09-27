"""Image-to-video with Veo via the Gemini API.
python3 gen_video.py OUT.mp4 IMAGE.png "motion prompt" [--dur 4] [--model veo-3.1-fast-generate-preview]
"""
import argparse, base64, io, json, os, sys, time, urllib.request, urllib.error
from PIL import Image

PRICE = {"veo-3.1-fast-generate-preview": 0.10, "veo-3.1-generate-preview": 0.40, "veo-3.1-lite-generate-preview": 0.05}
ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("image"); ap.add_argument("prompt")
ap.add_argument("--dur", type=int, default=4)
ap.add_argument("--model", default="veo-3.1-fast-generate-preview")
ap.add_argument("--res", default="720p")
ap.add_argument("--person", default="allow_adult")
ap.add_argument("--neg", default="music, speech, voices, text, subtitles, watermark, slow motion, faces, cartoon, CGI look, oversaturated")
a = ap.parse_args()
key = open(os.environ["GKEY_FILE"]).read().strip()
H = {"Content-Type": "application/json", "x-goog-api-key": key}
BASE = "https://generativelanguage.googleapis.com/v1beta"

im = Image.open(a.image).convert("RGB").resize((1280, 720), Image.LANCZOS)
buf = io.BytesIO(); im.save(buf, "PNG")
params = {"aspectRatio": "16:9", "durationSeconds": a.dur, "resolution": a.res}
if a.neg != "none": params["negativePrompt"] = a.neg
if a.person != "none": params["personGeneration"] = a.person
body = {"instances": [{"prompt": a.prompt, "image": {"bytesBase64Encoded": base64.b64encode(buf.getvalue()).decode(), "mimeType": "image/png"}}],
        "parameters": params}

def call(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=H)
    return json.load(urllib.request.urlopen(req, timeout=120))

t0 = time.time()
try:
    op = call(f"{BASE}/models/{a.model}:predictLongRunning", body)
except urllib.error.HTTPError as e:
    print("SUBMIT HTTP", e.code, e.read().decode()[:1000]); sys.exit(1)
name = op["name"]
while not op.get("done"):
    time.sleep(10)
    op = call(f"{BASE}/{name}")
if "error" in op:
    print("ERROR", json.dumps(op["error"])[:1000]); ok = False
else:
    r = op.get("response", {}).get("generateVideoResponse", {})
    samples = r.get("generatedSamples", [])
    ok = bool(samples)
    if ok:
        uri = samples[0]["video"]["uri"]
        req = urllib.request.Request(uri, headers={"x-goog-api-key": key})
        with urllib.request.urlopen(req, timeout=300) as resp, open(a.out, "wb") as f:
            f.write(resp.read())
    else:
        print("NO VIDEO", json.dumps(r)[:1000])
with open("spend.log", "a") as f:
    f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "kind": "video", "model": a.model, "dur": a.dur, "out": a.out, "ok": ok,
                        "usd_est": a.dur * PRICE.get(a.model, 0.4) if ok else 0}) + "\n")
print(("saved " + a.out) if ok else "FAILED", f"{time.time()-t0:.0f}s")
