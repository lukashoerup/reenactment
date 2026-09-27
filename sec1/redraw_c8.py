"""One-off: redraw c8 (bundle in the fire) from the photographic A-version frame (qa/S8_start.png) as a drawing,
with the gate; used after the plain prompt kept producing a body-like heap. Rejected versions stay as c8_rejected_r*.png."""
import sys, json, os
sys.argv=['keys.py','__none__']
src=open('sec1/keys.py').read().split("todo = [s for s in data")[0]
exec(src)
s=SH['c8']
refs=[part(p) for p in STYLE_REFS]+[part('qa/S8_start.png')]
txt=("Redraw the LAST reference image (a photograph) as a hand-made charcoal and ink drawing on warm grey paper, matching the "
     "drawing technique of the first two reference images exactly. Keep the composition: a shapeless heap of charred woollen "
     "blankets with one red-checked corner lying in a bonfire, flames at its edges. It must read only as a heap of blankets: "
     "no shoulder, no arm, no head, no human or animal outline. " + s['image_prompt'])
for t in range(2):
    r=call(IMG_MODEL, refs+[{"text":txt}], {"responseModalities":["IMAGE"],"imageConfig":{"aspectRatio":"16:9","imageSize":"2K"}})
    ok=False
    if r.ok:
        for c in r.json().get("candidates",[]):
            for p in c.get("content",{}).get("parts",[]):
                if p.get("inlineData"): open('sec1/kf/c8.png','wb').write(base64.b64decode(p["inlineData"]["data"])); ok=True
    log({"kind":"image","model":IMG_MODEL,"shot":"c8","ok":ok,"usd_est":0.134 if ok else 0})
    if not ok: print("draw failed", r.status_code, r.text[:200]); continue
    g=gate(s); print("gate", g)
    if g.get("pass"): break
    os.replace('sec1/kf/c8.png', f'sec1/kf/c8_rejected_r{t}.png')
