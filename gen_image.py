"""Generate a keyframe with Gemini image models. Usage:
python3 gen_image.py OUT.png "prompt" [--model M] [--ref a.png --ref b.png] [--size 2K]
Key is read from $GKEY_FILE. Logs every call to spend.log.
"""
import argparse, base64, json, os, sys, time, urllib.request, urllib.error

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("prompt")
ap.add_argument("--model", default="gemini-3-pro-image")
ap.add_argument("--ref", action="append", default=[])
ap.add_argument("--size", default="2K")
ap.add_argument("--aspect", default="16:9")
a = ap.parse_args()
key = open(os.environ["GKEY_FILE"]).read().strip()

parts = []
for r in a.ref:
    parts.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(open(r, "rb").read()).decode()}})
parts.append({"text": a.prompt})
body = {"contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"],
                             "imageConfig": {"aspectRatio": a.aspect, "imageSize": a.size}}}
url = f"https://generativelanguage.googleapis.com/v1beta/models/{a.model}:generateContent"
req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
t = time.time()
try:
    resp = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:800]); sys.exit(1)
saved = False
for c in resp.get("candidates", []):
    for p in c.get("content", {}).get("parts", []):
        d = p.get("inlineData") or p.get("inline_data")
        if d:
            open(a.out, "wb").write(base64.b64decode(d["data"])); saved = True
        elif p.get("text"):
            print("text:", p["text"][:300])
    if not saved: print("finish:", c.get("finishReason"), c.get("finishMessage", ""))
if not saved: print(json.dumps(resp.get("promptFeedback", {}))[:500])
um = resp.get("usageMetadata", {})
with open("spend.log", "a") as f:
    f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "kind": "image", "model": a.model, "size": a.size, "out": a.out, "ok": saved,
                        "usage": {k: um.get(k) for k in ("promptTokenCount", "candidatesTokenCount", "totalTokenCount")}}) + "\n")
print(("saved " + a.out) if saved else "NO IMAGE", f"{time.time()-t:.0f}s", um.get("candidatesTokenCount"))
