"""Blind whole-cut review of section 2 on Google Cloud: a Gemini model watches the cut with sound, gets the brief
and Lukas's criteria from section 1, and returns timestamped defects. Usage:
python3 sec2/judge_cut.py out/sec2_C_v1.mp4 [model] [fps]   -> sec2/judge_<model>.json
"""
import base64, json, os, subprocess, sys, time
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

video = sys.argv[1]; model = sys.argv[2] if len(sys.argv) > 2 else "gemini-3.1-pro-preview"
fps = float(sys.argv[3]) if len(sys.argv) > 3 else 3
KEY = os.environ["VERTEX_KEY_FILE"]; P = json.load(open(KEY))["project_id"]
c = service_account.Credentials.from_service_account_file(KEY, scopes=["https://www.googleapis.com/auth/cloud-platform"]); c.refresh(Request())
D = json.load(open("sec2/shots.json")); OFF = D["start"]
small = "sec2/_judge_480.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", "scale=854:480", "-c:v", "libx264", "-b:v", "300k",
                "-c:a", "aac", "-b:a", "64k", small], check=True)
shots = "\n".join(f'{i+1:>2} {s["start"]-OFF:6.1f}-{s["end"]-OFF:6.1f}s [{s["kind"]}] {s["image"] or "map from OpenStreetMap data"}'
                  f' | narration: "{s["line"]}"' for i, s in enumerate(D["shots"]))
prompt = f"""You are the picture editor and quality controller on a Danish true-crime documentary series.
Attached is a {D["end"]-OFF+D["tail"]:.0f}-second section of a re-enactment drawn in charcoal and ink on grey paper, cut to the episode's
real narration (Danish). The case: in September 1999 children found a woman's burned body wrapped in blankets in a bonfire in a
forest near Køge; police, a forensic pathologist and forensic technicians worked the scene in heavy rain; the body was taken to
Retsmedicinsk Institut (Teilum building, Frederik V's Vej, Copenhagen). This section covers the scene work and the transport.

The producer's notes on the previous section were: cuts too fast; too many AI-like movements (an object that did something
impossible, plastic appearing from nowhere, a half-floating bicycle); no close-ups of hands doing things; motion should be much
subtler; maps welcome but must be accurate. So this section uses long shots (8-18 s): drawings with a slow camera move and
rain/light added in post ('still'), two shots animated by a video model ('ambient', played at half speed), and two maps drawn
from OpenStreetMap data ('map'). The sound bed (rain) is added in post.

Shots (seconds from the start of the video):
{shots}

Series rules: no faces; no body, limbs, blood or injury, nothing that could be read as a body; nothing that could pass for real
archive footage; no readable text in drawings (map labels are intended); period-correct 1999; nothing may look AI-generated.

Watch the whole cut with sound. List every defect a demanding broadcast editor would notice: anything AI-like (morphing, objects
appearing, impossible physics, floating objects, uncanny motion), pacing (shots too long or too short for their line), picture
vs narration mismatch, continuity between shots, map legibility and accuracy of labels vs the narration, grade jumps, sound
problems (drop-outs, jumps at cuts, rain too loud or too quiet, anything fake), rule breaches. Do not list things that are fine.

Return JSON only: {{"defects":[{{"t_start":float,"t_end":float,"shot":int,"category":str,"severity":"blocker|major|minor",
"what":str,"fix":str}}],"pacing":str,"maps":str,"overall":str,"best_shot":int,"worst_shot":int}}"""
body = {"contents": [{"role": "user", "parts": [
    {"inlineData": {"mimeType": "video/mp4", "data": base64.b64encode(open(small, "rb").read()).decode()}, "videoMetadata": {"fps": fps}},
    {"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}}
url = f"https://aiplatform.googleapis.com/v1/projects/{P}/locations/global/publishers/google/models/{model}:generateContent"
t = time.time()
for attempt in range(6):
    r = requests.post(url, headers={"Authorization": f"Bearer {c.token}"}, json=body, timeout=900)
    if r.status_code in (429, 500, 503): time.sleep(40 * (attempt + 1)); continue
    break
if not r.ok: print("HTTP", r.status_code, r.text[:800]); sys.exit(1)
j = r.json(); txt = "".join(p.get("text", "") for p in j["candidates"][0]["content"]["parts"]); um = j.get("usageMetadata", {})
out = f"sec2/judge_{model}.json"; open(out, "w").write(txt)
usd = (um.get("promptTokenCount", 0) * 2 + (um.get("candidatesTokenCount", 0) + um.get("thoughtsTokenCount", 0)) * 12) / 1e6
with open("spend.log", "a") as f:
    f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "backend": "vertex", "section": "sec2", "kind": "judge-cut", "model": model,
                        "usd_est": round(usd, 3), "tokens_in": um.get("promptTokenCount")}) + "\n")
print(out, f"{time.time()-t:.0f}s", um.get("promptTokenCount"), "tokens in", f"~${usd:.2f}")
