"""Build the review page for section 1 (artifact "Det Brændende Lig 0:00–5:06").
python3 page2/build.py   -> page2/index.html (storyboard data from sec1/shots.json, picks, rejected keyframes)
Media (page2/hls/, page2/thumbs/, page2/poster.jpg) is made separately and never committed.
"""
import html, json, os

shots = json.load(open("sec1/shots.json"))["shots"]
picks = json.load(open("sec1/picks.json"))
redrawn = {f.split("_rejected")[0] for f in os.listdir("sec1/kf") if "_rejected" in f}
reanimated = {k for k, v in picks.items() if v.get("round") == 2}
FROM_TEST = {"c1", "c3", "c5", "c6", "c7", "s36"}
WEAK = {   # what a viewer should know about a shot, in plain Danish
    "s06": "Regnen mangler. Forsøgene med regn blinkede, så jeg valgte det rolige.",
    "s13": "Mærket på flasken kan ligne et dødningehoved.",
    "c2": "Regnen mangler. Forsøgene med regn blinkede, så jeg valgte det rolige.",
    "c5": "Fra testen: flammerne hvirvler lidt tegnefilm-agtigt.",
    "c6": "Fra testen: et barn går ud af billedet.",
    "s38": "To betjente bagfra, hvor der kun var bedt om én.",
    "s41": "Lidt langsommere end normalt (0,87×), og telefonen ringer videre, når røret løftes.",
    "s42": "Videoen har selv lagt politiradio på lyden.",
}

def tc(t):
    m, s = divmod(int(t), 60)
    return f"{m}:{s:02d}"

def line(s):
    t = s["line"].replace("(music)", "(musik)").strip()
    return t if len(t) <= 120 else t[:117].rsplit(" ", 1)[0] + " …"

cards = []; i = 0
for s in shots:
    if s["image"] == "BLACK":
        continue
    i += 1
    tags = []
    if s["id"] in FROM_TEST: tags.append(("old", "Fra testen"))
    elif s["kind"] == "reuse": tags.append(("old", "Genbrugt"))
    if s["id"] in redrawn: tags.append(("fix", "Tegnet om"))
    if s["id"] in reanimated: tags.append(("fix", "Animeret om"))
    if s["id"] in WEAK: tags.append(("weak", "Svaghed"))
    tag_html = "".join(f'<span class="tag {k}">{v}</span>' for k, v in tags)
    weak = f'<p class="weak-note">{html.escape(WEAK[s["id"]])}</p>' if s["id"] in WEAK else ""
    cards.append(
        f'<li><button class="shot" type="button" data-t="{s["start"]:.2f}" aria-label="Spring til {tc(s["start"])}">'
        f'<img src="thumbs/{s["id"]}.jpg" alt="" loading="lazy" width="320" height="180">'
        f'<span class="tcode">{tc(s["start"])}</span></button>'
        f'<div class="meta"><span class="no">Skud {i}</span>{tag_html}</div>'
        f'<p class="vo">{html.escape(line(s))}</p>{weak}</li>')

n_new = sum(1 for s in shots if s["kind"] == "new" and s["image"] != "BLACK")
n_rej = sum(1 for f in os.listdir("sec1/kf") if "_rejected" in f)
n_takes = sum(1 for f in os.listdir("sec1/clips") if f.endswith(".mp4") and "_use" not in f)
tpl = open("page2/index.template.html").read()
out = (tpl.replace("{{CARDS}}", "\n".join(cards))
          .replace("{{N_SHOTS}}", str(i))
          .replace("{{N_NEW}}", str(n_new))
          .replace("{{N_REJ}}", str(n_rej))
          .replace("{{N_TAKES}}", str(n_takes))
          .replace("{{N_REANIM}}", str(len(reanimated)))
          .replace("{{N_REDRAWN}}", str(len(redrawn))))
open("page2/index.html", "w").write(out)
print("page2/index.html", len(out), "bytes,", len(cards), "cards")
