"""Post-process 3D frames as they land, so the edit is ready when rendering ends."""
import os, glob, json, time
import post

ROOT = os.path.dirname(os.path.abspath(__file__))
SHOTS = ["S1", "S3", "S5", "S8"]
rains = {s: post.Rain(seed=sum(map(ord, s)) % 1000) for s in SHOTS}

def done():
    p = os.path.join(ROOT, "render_progress.txt")
    return os.path.exists(p) and "ALLDONE" in open(p).read()

while True:
    finished = done()
    for s in SHOTS:
        src = os.path.join(ROOT, "render", s)
        mp = os.path.join(src, "meta.json")
        if not os.path.exists(mp):
            continue
        meta = json.load(open(mp))
        first = min(int(k) for k in meta)
        out = os.path.join(ROOT, "post", s); os.makedirs(out, exist_ok=True)
        files = sorted(glob.glob(os.path.join(src, "f_*.exr")))
        for p in files[:-1] if not finished else files:  # the newest file may still be writing
            f = int(os.path.basename(p)[2:6])
            dst = os.path.join(out, f"p_{f - first:04d}.png")
            if os.path.exists(dst):
                continue
            rgb, mist = post.read_exr(p)
            post.write_png(dst, post.process_frame(rgb, mist, meta.get(str(f)), f, rains[s]))
    if finished:
        break
    time.sleep(20)
print("POSTDONE")
