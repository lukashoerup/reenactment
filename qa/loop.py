"""Automatic fix loop for one or more shots, no human in it:
  generate a take -> AI judge watches the part we will use -> pass: keep
  fail: regenerate once with the judge's own fix -> still fail: fall back to the still (method B).
Stops before any call that would push spend past the cap.

python3 qa/loop.py S2 S4 S8
"""
import base64, json, os, subprocess, sys, time, urllib.request, urllib.error

KEY = open(os.environ["GKEY_FILE"]).read().strip()
BASE = "https://generativelanguage.googleapis.com/v1beta"
CAP_USD = float(os.environ.get("CAP_USD", "1.10"))       # list price; ≈ 8.8 kr incl. VAT
VIDEO_MODEL = "veo-3.1-lite-generate-preview"; VIDEO_USD_S = 0.05
JUDGE_MODEL = "gemini-3.1-pro-preview"; JUDGE_USD = 0.06   # measured ≈ 0.045–0.075 per call
MAX_TAKES = 2
spent = 0.0
log = open("qa/loop.log", "a")

def say(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.write(s + "\n"); log.flush()

STILL = ("Documentary re-enactment shot on 35mm film, 1999. Static composition. Nothing and nobody enters the frame: "
         "no hands, no sticks, no tools, no logs thrown in, no people anywhere, not even off-screen. "
         "Nothing is added to or taken from the fire. No sudden flare-ups, no bursts of smoke.")
SHOTS = {
  "S2": dict(image="kf/S2_v1.png", use=(0.0, 4.0), line="Selvom regnen står ned i stænger, buldrer ilden lystigt. (Even though the rain is pouring down, the fire roars merrily.)",
             brief="A large unattended bonfire burning in a hollow in a beech forest at dusk in heavy rain. Nobody is there.",
             prompt=STILL + " Locked-off camera. Heavy rain is clearly visible as bright streaks falling through the firelight "
                    "and splashing on the wet leaves. The bonfire burns steadily and naturally, flames flickering, thin steam "
                    "drifting up where rain hits the embers. Audio: heavy rain, crackling fire, hiss of rain on embers. No music, no voices."),
  "S4": dict(image="kf/S4_v2.png", use=(0.5, 2.9), line="På cirka 70 centimeter. (About 70 centimetres.)",
             brief="Close-up of a bundle of charred woollen blankets (one red-checked corner) lying in the bonfire. Nothing inside is visible. Nobody is there.",
             prompt=STILL + " Very slow, smooth sideways drift of the camera. Small flames lick along the charred wool, embers glow "
                    "and fade, raindrops sizzle and thin smoke rises. The bundle itself stays completely still and unchanged: "
                    "it is only wrapped fabric. Audio: close crackle of embers, sizzle of rain. No music, no voices."),
  "S8": dict(image="qa/S8_start.png", use=(1.0, 2.5), line="Eller et menneske? (Or a human being?)",
             brief="Closer on the same charred blanket bundle (same red-checked corner as S4) in the fire; flames rise in front of it. It must read as wrapped fabric, never as a body shape.",
             prompt=STILL + " Very slow push-in toward the charred blanket bundle. Flames slowly rise and grow in the foreground "
                    "and around its edges, heat shimmer, rain streaks glowing orange. The bundle does not move and does not change "
                    "shape: it stays a heap of charred wool blankets. Audio: fire building up, rain. No music, no voices."),
}

def post(url, body, timeout=600):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    return json.load(urllib.request.urlopen(req, timeout=timeout))

def get(url):
    req = urllib.request.Request(url, headers={"x-goog-api-key": KEY})
    return json.load(urllib.request.urlopen(req, timeout=120))

def generate(shot, prompt, out):
    global spent
    from PIL import Image; import io
    im = Image.open(SHOTS[shot]["image"]).convert("RGB").resize((1280, 720), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "PNG")
    body = {"instances": [{"prompt": prompt, "image": {"bytesBase64Encoded": base64.b64encode(buf.getvalue()).decode(), "mimeType": "image/png"}}],
            "parameters": {"aspectRatio": "16:9", "durationSeconds": 4, "resolution": "720p", "personGeneration": "allow_adult"}}
    op = post(f"{BASE}/models/{VIDEO_MODEL}:predictLongRunning", body)
    while not op.get("done"):
        time.sleep(8); op = get(f"{BASE}/{op['name']}")
    if "error" in op:
        say("  generate error:", json.dumps(op["error"])[:300]); return False
    s = op.get("response", {}).get("generateVideoResponse", {}).get("generatedSamples", [])
    if not s:
        say("  no video:", json.dumps(op.get("response", {}))[:300]); return False
    req = urllib.request.Request(s[0]["video"]["uri"], headers={"x-goog-api-key": KEY})
    open(out, "wb").write(urllib.request.urlopen(req, timeout=300).read())
    spent += 4 * VIDEO_USD_S
    return True

def judge(shot, clip):
    global spent
    a, b = SHOTS[shot]["use"]
    part = clip.replace(".mp4", "_use.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(b - a), "-i", clip, "-c:v", "libx264", "-crf", "20", "-c:a", "aac", part], check=True)
    use_ref = shot in ("S4", "S8")
    ref = base64.b64encode(open("qa/ref_bundle.jpg", "rb").read()).decode() if use_ref else None
    prompt = f"""You are the strict quality controller on a Danish broadcast true-crime documentary. The attached video is ONE
AI-generated re-enactment shot, exactly the part that will be used in the edit.{" The attached still is the continuity reference for the bundle (charred woollen blankets with one red-checked corner)." if use_ref else " This shot comes BEFORE the bundle is revealed: the bundle must not be visible here, and no reference applies."}

Story: two children found an unattended bonfire in a beech forest near Køge at dusk in heavy rain, September 1999.
Nobody else is present. In the fire lies a ~70 cm bundle of wrapped blankets; nothing inside may ever be visible.
This shot: {SHOTS[shot]['brief']}
Narration over it: "{SHOTS[shot]['line']}"

FAIL the shot if ANY of these happen, even for a few frames:
- anything enters the frame or is moved by an unseen hand (sticks, logs, tools, hands) or anything implies a person
- (only if the bundle is in this shot) it changes shape, reads as a body/torso/limb/animal, or stops matching the reference
- morphing, melting, flicker, objects appearing/disappearing, impossible physics, pareidolia (faces in textures)
- it looks CGI, glossy or AI-generated; sudden flare-ups or smoke bursts that look fake
- the picture fights the narration line
Minor imperfections a viewer would not notice are OK.

Return JSON only: {{"pass": bool, "score": 0-10, "defects": [str], "fix": "one or two sentences to add to the video
generation prompt that would prevent the defects"}}"""
    body = {"contents": [{"parts": [
                {"inline_data": {"mime_type": "video/mp4", "data": base64.b64encode(open(part, "rb").read()).decode()}, "video_metadata": {"fps": 12}},
                *([{"inline_data": {"mime_type": "image/jpeg", "data": ref}}] if ref else []),
                {"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}}
    r = post(f"{BASE}/models/{JUDGE_MODEL}:generateContent", body)
    spent += JUDGE_USD
    txt = "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"])
    v = json.loads(txt)
    return v[0] if isinstance(v, list) else v

results = {}
for shot in sys.argv[1:]:
    prompt = SHOTS[shot]["prompt"]; results[shot] = {"final": None, "takes": []}
    for take in range(1, MAX_TAKES + 1):
        if spent + 4 * VIDEO_USD_S + JUDGE_USD > CAP_USD:
            say(f"{shot}: budget cap reached (${spent:.2f}), stopping takes"); break
        out = f"clips/{shot}_L{take}.mp4"
        say(f"{shot} take {take}: generating ...")
        ok = False
        for attempt in range(3):
            try:
                ok = generate(shot, prompt, out); break
            except urllib.error.HTTPError as e:
                msg = e.read().decode()[:200]
                if e.code == 429 and attempt < 2:
                    say("  rate limited, waiting 75 s"); time.sleep(75); continue
                say(f"  HTTP {e.code}: {msg}"); break
        if not ok: break
        v = judge(shot, out)
        results[shot]["takes"].append({"take": take, "file": out, **v})
        say(f"  judge: pass={v['pass']} score={v['score']} defects={v['defects']}")
        if v["pass"]:
            results[shot]["final"] = out; break
        prompt = SHOTS[shot]["prompt"] + " " + v.get("fix", "")
        say(f"  retry with fix: {v.get('fix','')}")
    if not results[shot]["final"]:
        results[shot]["final"] = f"clips/{shot}_B.mp4"
        say(f"{shot}: no take passed -> fallback to still with camera move (method B)")
    say(f"{shot}: FINAL {results[shot]['final']}   spent so far ${spent:.2f}")
json.dump(results, open("qa/loop_results.json", "w"), indent=1)
say(f"DONE total ${spent:.2f} (~{spent*6.4*1.25:.1f} kr incl. VAT)")
