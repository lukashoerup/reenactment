"""Build the review page for section 2 (artifact "Det Brændende Lig 5:06–9:02").
python3 page3/build.py   -> page3/index.html (storyboard from sec2/shots.json, rejected keyframes, spend.log)
Media (page3/hls/, page3/thumbs/, page3/poster.jpg) is made separately and never committed.
"""
import html, json, os

D = json.load(open("sec2/shots.json")); shots = D["shots"]; OFF = shots[0]["start"]; SH = {s["id"]: s for s in shots}
redrawn = {f.split("_rejected")[0] for f in os.listdir("sec2/kf") if "_rejected" in f}
KIND = {"still": ("cam", "Tegning + kamera"), "ambient": ("anim", "Animeret"), "map": ("map", "Kort")}
WJ = json.load(open("page3/weak.json")) if os.path.exists("page3/weak.json") else {"cards": {}, "list": []}
WEAK = WJ["cards"]

def tc(t):
    m, s = divmod(int(t), 60)
    return f"{m}:{s:02d}"

def line(s):
    t = s["line"].strip()
    return t if len(t) <= 130 else t[:127].rsplit(" ", 1)[0] + " …"

cards = []
for i, s in enumerate(shots, 1):
    k, lab = KIND[s["kind"]]
    tags = [(k, lab)]
    if s["id"] in redrawn: tags.append(("fix", "Tegnet om"))
    if s["id"] in WEAK: tags.append(("weak", "Svaghed"))
    tag_html = "".join(f'<span class="tag {c}">{v}</span>' for c, v in tags)
    weak = f'<p class="weak-note">{html.escape(WEAK[s["id"]])}</p>' if s["id"] in WEAK else ""
    dur = s["end"] - s["start"]
    cards.append(
        f'<li><button class="shot" type="button" data-t="{s["start"] - OFF:.2f}" aria-label="Spring til {tc(s["start"])}">'
        f'<img src="thumbs/{s["id"]}.jpg" alt="" loading="lazy" width="320" height="180">'
        f'<span class="tcode">{tc(s["start"])} · {dur:.0f} s</span></button>'
        f'<div class="meta"><span class="no">Skud {i}</span>{tag_html}</div>'
        f'<p class="vo">{html.escape(line(s))}</p>{weak}</li>')

spent = 0.0; n_img = 0
for l in open("spend.log"):
    try: d = json.loads(l)
    except Exception: continue
    if d.get("section") == "sec2":
        spent += d.get("usd_est", 0) or 0
        if d.get("kind") == "image" and d.get("ok"): n_img += 1
dur = shots[-1]["end"] - OFF
tpl = open("page3/index.template.html").read()
rep = {"CARDS": "\n".join(cards), "N_SHOTS": str(len(shots)), "AVG": f"{dur / len(shots):.0f}".replace(".", ","),
       "N_STILL": str(sum(s["kind"] == "still" for s in shots)), "N_ANIM": str(sum(s["kind"] == "ambient" for s in shots)),
       "N_MAP": str(sum(s["kind"] == "map" for s in shots)), "N_IMG": str(n_img),
       "N_REJ": str(sum(1 for f in os.listdir("sec2/kf") if "_rejected" in f)),
       "USD": f"{spent:.0f}", "KR": f"{round(spent * 8 / 10) * 10:.0f}", "KR_MIN": f"{spent * 8 / (dur / 60):.0f}",
       "OFF": f"{OFF}", "KR_EP": f"{round(spent * 8 / (dur / 60) * 44.6 / 100) * 100:,.0f}".replace(",", "."),
       "WEAK_LIST": "\n".join(
           f'        <li><strong>{html.escape(w["title"])}</strong> {html.escape(w["text"])} ' +
           " ".join(f'<button class="jump" type="button" data-t="{SH[i]["start"] - OFF:.2f}">{tc(SH[i]["start"])}</button>' for i in w["ids"]) +
           "</li>" for w in WJ["list"])}
for k, v in rep.items(): tpl = tpl.replace("{{" + k + "}}", v)
open("page3/index.html", "w").write(tpl)
print("page3/index.html", len(tpl), "bytes;", f"spend ${spent:.2f}", rep["KR_MIN"], "kr/min")
