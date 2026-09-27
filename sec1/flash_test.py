"""One-off: can gemini-3.1-flash-image (separate quota) match the drawn style? Draws s55 to qa/flash_s55.png. Answer: yes."""
import sys, os
sys.argv=['keys.py','__none__']
src=open('sec1/keys.py').read().split("todo = [s for s in data")[0]
exec(src)
IMG_MODEL="gemini-3.1-flash-image"
s=SH['s55']
refs=[part(p) for p in STYLE_REFS]
txt="Match the drawing technique, paper, line quality and palette of the first two reference images exactly. "+s['image_prompt']
r=call(IMG_MODEL, refs+[{"text":txt}], {"responseModalities":["IMAGE"],"imageConfig":{"aspectRatio":"16:9","imageSize":"2K"}})
ok=False
if r.ok:
    for c in r.json().get("candidates",[]):
        for p in c.get("content",{}).get("parts",[]):
            if p.get("inlineData"): open('qa/flash_s55.png','wb').write(base64.b64decode(p["inlineData"]["data"])); ok=True
log({"kind":"image","model":IMG_MODEL,"shot":"s55-test","ok":ok,"usd_est":0.10 if ok else 0})
print("ok" if ok else (r.status_code, r.text[:200]))
