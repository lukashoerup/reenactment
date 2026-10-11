"""Build the review page for method E scenes: page/gfx/index.html + small videos + posters.

    python3 -m gfx.review_page episodes/braendende-lig/scenes/S1-fundet.json ...

Videos are re-encoded from out/gfx/<id>_720_clean.mp4 with the episode audio to fit the
artifact's 15 MB per-file limit. The page is published with the Artifact tool (files: the
mp4s and jpgs next to index.html).
"""
import html, json, os, subprocess, sys

from .render import load_scene, build, REPO
from .timing import fmt_tc

OUT = os.path.join(REPO, "page", "gfx")
LIMIT = 13.8e6  # bytes, under the 15 MB file limit


def esc(s):
    return html.escape(str(s or ""), quote=True)


def what(s):
    p = s["spec"]["p"]
    t = s["type"]
    if t == "map":
        bits = [m.get("label") for m in p.get("markers", []) if m.get("label")]
        if p.get("caption"):
            h = p["caption"].get("h", "")
            bits.insert(0, " ".join(h) if isinstance(h, list) else h)
        if p.get("routes"):
            bits.append("rute")
        if p.get("rings"):
            bits.append("zone")
        return "Kort: " + ", ".join(b for b in bits if b)
    if t == "siteplan":
        labs = [i.get("label") for i in p.get("items", []) if i.get("label")]
        labs += [w["text"] for w in p.get("words", [])][:3]
        if p.get("caption"):
            labs.insert(0, p["caption"].get("h"))
        return "Skitse af fundstedet" + (": " + ", ".join(l for l in labs if l) if labs else " (ingen tekst)")
    if t == "facts":
        return f"{p.get('heading', '')}: " + " · ".join(i["text"] for i in p.get("items", []))
    if t == "quote":
        words = " ".join(w[0] for w in p.get("words", []))
        return "Citat" + (f" ({p['who']})" if p.get("who") else "") + ": »" + (words[:110] + ("…" if len(words) > 110 else "")) + "«"
    if t == "title":
        return " ".join(p.get("lines", []))
    if t == "diorama":
        bits = [i.get("text") or i.get("label") for i in p.get("items", []) if i.get("type") in ("label", "text3d", "steps", "tracks") and (i.get("text") or i.get("label"))]
        if p.get("caption"):
            bits.insert(0, p["caption"].get("h"))
        if any(i.get("type") == "car" for i in p.get("items", [])):
            bits.append("bilen kører fra stedet")
        return "3D-model af fundstedet" + (": " + ", ".join(b for b in bits if b) if bits else " (ingen tekst)")
    if t == "object":
        return {"bottle": "Model: flaske tændvæske", "cast": "Model: gipsafstøbning af dækspor"}.get(p.get("model"), "Model")
    return t


def encode(src_clean, a0, a1, out_mp4, bed, bed_db):
    d = a1 - a0
    kbps = int((LIMIT * 8 / d - 96000) / 1000)
    ep_audio = os.path.join(REPO, "audio", "episode.mp3")
    if bed == "rain":
        extra = ["-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.6:seed=7:duration={d:.3f},highpass=f=350,lowpass=f=5200"]
        mix = f"[1:a]volume={bed_db}dB[b];[0:a][b]amix=inputs=2:normalize=0,afade=t=out:st={d - 0.3:.3f}:d=0.3[a]"
        vi = 2
    else:
        extra, mix, vi = [], f"[0:a]afade=t=out:st={d - 0.3:.3f}:d=0.3[a]", 1
    common = ["ffmpeg", "-v", "error", "-y", "-ss", f"{a0:.3f}", "-t", f"{d:.3f}", "-i", ep_audio, *extra, "-i", src_clean,
              "-filter_complex", mix + f";[{vi}:v]scale=960:540,vignette=angle=0.42[v]", "-map", "[v]", "-map", "[a]",
              "-c:v", "libx264", "-preset", "medium", "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.6)}k",
              "-bufsize", f"{kbps * 2}k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-ac", "1"]
    log = out_mp4 + ".log"
    subprocess.run(common + ["-pass", "1", "-passlogfile", log, "-an", "-f", "mp4", "/dev/null"], check=True)
    subprocess.run(common + ["-pass", "2", "-passlogfile", log, "-movflags", "+faststart", out_mp4], check=True)
    for f in os.listdir(OUT):
        if f.startswith(os.path.basename(log)):
            os.remove(os.path.join(OUT, f))


def main(paths):
    os.makedirs(OUT, exist_ok=True)
    scenes = []
    for p in paths:
        scene, case, tx, ep_dir = load_scene(p)
        scene["_path"] = os.path.abspath(p)
        a0, a1, shots = build(scene, case, tx)
        clean = os.path.join(REPO, "out", "gfx", f"{scene['id']}_720_clean.mp4")
        vid = os.path.join(OUT, f"{scene['id']}.mp4")
        if not os.path.exists(vid) or os.path.getmtime(vid) < os.path.getmtime(clean):
            encode(clean, a0, a1, vid, scene.get("bed", "rain"), scene.get("bed_db", -31))
        poster = os.path.join(OUT, f"{scene['id']}.jpg")
        mid = next((s for s in shots if s["type"] in ("map", "quote")), shots[0])
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{mid['start'] - a0 + mid['dur'] * 0.7:.2f}", "-i", clean,
                        "-frames:v", "1", "-vf", "scale=960:540", "-q:v", "4", poster], check=True)
        scenes.append({"scene": scene, "a0": a0, "a1": a1, "shots": shots, "size": os.path.getsize(vid)})
        print(scene["id"], f"{os.path.getsize(vid) / 1e6:.1f} MB")
    json.dump([{"id": s["scene"]["id"], "title": s["scene"]["title"], "from": fmt_tc(s["a0"]), "to": fmt_tc(s["a1"]),
                "note": s["scene"].get("summary") or s["scene"].get("note", ""),
                "shots": [{"id": x["id"], "tc": fmt_tc(x["start"]), "dur": round(x["dur"], 1), "type": x["type"],
                           "what": what(x), "src": x["spec"].get("credit", "")} for x in s["shots"]]}
               for s in scenes], open(os.path.join(OUT, "scenes.json"), "w"), ensure_ascii=False, indent=1)
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "review_template.html")).read()
    data = json.load(open(os.path.join(OUT, "scenes.json")))
    open(os.path.join(OUT, "index.html"), "w").write(tpl.replace("/*SCENES*/[]", json.dumps(data, ensure_ascii=False)))
    print("wrote", os.path.join(OUT, "index.html"))


if __name__ == "__main__":
    main(sys.argv[1:])
