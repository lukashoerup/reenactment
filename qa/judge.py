"""Blind AI review of a cut: sends the video (with sound) plus the brief to a Gemini model
and asks for a timestamped defect list. Usage: python3 qa/judge.py VIDEO.mp4 MODEL OUT.json [fps]"""
import base64, json, os, sys, time, urllib.request, urllib.error

video, model, out = sys.argv[1], sys.argv[2], sys.argv[3]
fps = float(sys.argv[4]) if len(sys.argv) > 4 else 6
key = open(os.environ["GKEY_FILE"]).read().strip()
sl = json.load(open("shotlist.json"))

narr = """00.0-01.1 (music)
01.1-04.5 "Bålets flammer lokker de nysgerrige børn tættere på." (The bonfire's flames lure the curious children closer.)
05.3-08.8 "Selvom regnen står ned i stænger, buldrer ilden lystigt." (Even though the rain is pouring down, the fire roars merrily.)
09.4-11.3 "Midt i bålet ligger en bylt." (In the middle of the fire lies a bundle.)
11.8-13.3 "På cirka 70 centimeter." (About 70 centimetres.)
14.5-15.2 "Hvad er det?" (What is it?)
16.2-17.0 "Et dyr?" (An animal?)
18.6-19.4 "Affald?" (Rubbish?)
20.0-21.3 "Eller et menneske?" (Or a human being?)"""

shots = "\n".join(f'{s["id"]} {s["start"]:.2f}-{s["end"]:.2f}s: {s["action"]}' for s in sl["shots"])

prompt = f"""You are the picture editor and quality controller on a Danish true-crime documentary series.
Attached is a 22-second re-enactment cut for the cold open of an episode about a woman's body found burning
in a bonfire in a beech forest near Køge in September 1999. The picture is fully AI-generated; the sound is the
episode's real narration with rain/fire ambience underneath.

The story in this scene: two children (an older one in a navy rain jacket, a smaller one in a red rain jacket),
playing in the forest in heavy rain at dusk, find a far-too-large bonfire with a bundle of blankets in it. Nobody
else is present. The bundle is ~70 cm of wrapped fabric; nothing inside may ever be visible.

Narration timing (seconds from the start of the video):
{narr}

Intended shot list:
{shots}

Series rules: no recognisable faces; no body, limbs, blood or injury; nothing that could pass for real archive
footage; no readable text; period-correct for 1999; it must never look AI-generated, glossy or like CGI.

Watch the whole cut carefully, frame by frame where needed, and with sound. List EVERY defect a demanding
broadcast editor or a sharp-eyed viewer would notice, including:
- anything that looks AI-generated (morphing, melting, objects appearing/disappearing, impossible physics,
  pareidolia such as faces appearing in textures, uncanny motion)
- actions or objects not in the story (e.g. unexplained things entering frame, implied extra people)
- continuity between shots (costume, sizes of the children, boots, the bundle's look, fire size, time of day, positions)
- mismatch between picture and narration (timing of cuts vs. words, whether each image supports its line)
- scale and plausibility (distances, fire size relative to the children)
- grade/exposure jumps between shots, sound problems (drop-outs, jumps at cuts, anything that sounds fake)
- rule breaches
Do not list things that are fine. Be specific and use timestamps.

Return JSON only: {{"defects":[{{"t_start":float,"t_end":float,"shot":"S1".."S9","category":str,
"severity":"blocker|major|minor","what":str,"fix":str}}],"overall":str,"best_shot":str,"worst_shot":str}}
The "fix" must be a concrete regeneration or edit instruction (new prompt wording, trim, re-grade, swap take)."""

data = base64.b64encode(open(video, "rb").read()).decode()
body = {"contents": [{"parts": [
            {"inline_data": {"mime_type": "video/mp4", "data": data}, "video_metadata": {"fps": fps}},
            {"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}}
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
t = time.time()
try:
    r = json.load(urllib.request.urlopen(req, timeout=600))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:1500]); sys.exit(1)
txt = "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"])
um = r.get("usageMetadata", {})
open(out, "w").write(txt)
with open("spend.log", "a") as f:
    f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "kind": "judge", "model": model, "ok": True,
                        "usage": {k: um.get(k) for k in ("promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount", "totalTokenCount")}}) + "\n")
print(model, f"{time.time()-t:.0f}s", um.get("promptTokenCount"), "in /", um.get("candidatesTokenCount"), "out /", um.get("thoughtsTokenCount"), "think")
