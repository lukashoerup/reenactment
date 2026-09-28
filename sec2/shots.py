"""Section 2 of Danske Drabssager "Det Brændende Lig": 5:06.3–9:01.5, drawn style (C), one version.
Lukas's notes on section 1 (2026-09-28): fewer, longer, slower shots; much subtler motion; no close-ups of hands
doing things; nothing floating; maps only from real map data. Writes sec2/shots.json.

kind: still   -> keyframe + slow sub-pixel camera move + procedural rain / light, drawn at 12 fps (sec2/move.py, free)
      ambient -> keyframe + Veo 3.1 Lite, first = last frame, audio off, 6 s played at ~0.5x (sec2/clips.py)
      map     -> OpenStreetMap vector data drawn in the same charcoal look (sec2/maps.py), no image model
move: camera from a=(cx, cy, zoom) to b=(cx, cy, zoom); cx, cy = centre in 0..1 of the keyframe, zoom 1 = full frame
fx:   rain = 0..1 amount, flicker = orange light sources breathe, blue = emergency light pulses
audio: ext = rain bed, int = the rain muffled behind walls
Times are on the episode clock; cuts sit in the pauses of the narration (word timings in audio/seg_0610_1030.json).
"""
import json

STYLE = ("Hand-made documentary illustration: charcoal and black ink wash on warm grey paper, loose confident "
         "strokes, visible paper grain and smudges, mostly monochrome grey and black. The only colour is warm "
         "orange-yellow soft pastel for light sources (lanterns, lamps, headlights, lit windows); emergency lights may "
         "use one muted blue pastel. Reportage-sketch look like a courtroom sketch artist: not digital painting, "
         "not anime, not a comic. Denmark, late September 1999, night, rain. No readable text, letters or numbers "
         "anywhere, no logos. No faces: people only from behind or in silhouette, small in the frame, standing still, "
         "hands not visible. Every object rests on the ground or hangs from something; nothing floats. 16:9 composition.")
MOTION = ("Animated hand-drawn charcoal and ink illustration: every frame keeps exactly the same drawn style, "
          "paper texture and pastel colours as the image; it never turns photographic or cartoonish. "
          "Static shot, the camera does not move. Very slow, very subtle motion. ")
NEG = ("person, hand, arm, face, body, animal, thrown object, flying object, falling object, moving object, "
       "camera movement, zoom, text, letters, numbers, logo, cartoon, anime, photograph, flash, sparks")
STILL_TXT = (" This drawing is a still frame that will not be animated: draw nothing that only looks right when moving —"
             " no open flames, no pouring or splashing water, no smoke plumes; rain only as fine diagonal pencil strokes.")
MONO_TXT = " This image has no warm light source: keep it entirely monochrome grey and black, with no orange at all."

def S(id, a, b, line, kind, img="", mot="", move=None, fx=None, ref=None, audio="ext", mono=False):
    return dict(id=id, start=a, end=b, line=line, kind=kind, image=img, motion=mot,
                move=move or dict(a=(.5, .5, 1.0), b=(.5, .5, 1.08)), fx=fx or {}, ref=ref, audio=audio, mono=mono)

PUSH = lambda z=1.08, cx=.5, cy=.5: dict(a=(.5, .5, 1.0), b=(cx, cy, z))
PULL = lambda z=1.12, cx=.5, cy=.5: dict(a=(cx, cy, z), b=(.5, .5, 1.0))

SHOTS = [
 S("t01", 306.3, 315.8, "Det var også mange spor … både fra heste, fodgængere og løbere og så videre.", "still",
   "Low close view along a muddy forest path at dusk: many overlapping hoofprints, boot prints and running-shoe prints "
   "pressed into the mud, some filled with rainwater, wet beech leaves; the path leads away into grey beech trunks; no people.",
   move=PUSH(1.10, .5, .42), fx=dict(rain=.6), mono=True),
 S("t02", 315.8, 327.4, "…fik man dæmmet, slukket ilden, sikret sporene og fik kriminalteknikerne ud for at finde spor i skovbunden.", "still",
   "The hollow in the beech forest at night, seen from a few metres away: the extinguished bonfire under a dark tarpaulin "
   "stretched on wooden poles, a low flat circle of black charred branches and wet grey ash, two hurricane lanterns hanging "
   "from the poles, a row of small plain white marker flags on thin sticks stuck in the mud around it; no smoke; no people.",
   # was 'ambient' (Veo smoke): the whole-cut judge saw the smoke morph and bubble (2026-09-28)
   move=PUSH(1.07, .5, .5), fx=dict(rain=.6, flicker=.4, dry=[[(.34, .30), (.70, .24), (.86, .58), (.34, .62)]]), ref="s48"),
 S("t03", 327.4, 337.7, "Når et lig bliver fundet og der er mistanke om drab, bliver en retsmediciner altid tilkaldt. Hans Petter Hougen …", "still",
   "A dark 1990s estate car without any badge parked on a muddy forest track at night at the edge of a beech forest, "
   "headlights on, all doors closed, heavy rain visible in the headlight beams, the faint glow of lanterns far away between "
   "the trees; nobody visible.",
   move=PUSH(1.09, .46, .52), fx=dict(rain=.9)),
 S("t04", 337.7, 348.6, "Det var et slukket bål i en skov, og oven på dette bål så lå der en bylt.", "still",
   "Seen from about ten metres away through wet hanging branches: the extinguished bonfire in the hollow under the dark "
   "tarpaulin on poles, a low flat mound of black charred branches and grey ash lit by one hanging hurricane lantern; "
   "nothing on the ash can be made out; rain; no people.",
   move=PUSH(1.07), fx=dict(rain=.7, flicker=.5,
       dry=[[(.30, .45), (.55, .30), (.66, .30), (.74, .55), (.66, .62), (.25, .62)]]), ref="s48"),
 S("t05", 348.6, 361.4, "…der så ud til at være noget stof, måske nogle tæpper, og det var delvis brændt i stykker.", "still",
   "Extreme close-up: a charred, torn scrap of red-and-black checked woollen blanket lying flat on wet grey ash, burnt holes "
   "and blackened frayed edges, raindrops beaded on the wool; the fire is completely out: no flames, no glowing embers; "
   "only fabric and ash fill the frame.",
   # was 'ambient': every Veo take drew raindrops as cartoon teardrops and white splash stars (2026-09-28)
   move=PUSH(1.07, .5, .5), fx=dict(rain=.35), ref="c4", mono=False),
 S("t06", 361.4, 374.5, "…om det var noget, der havde været levende, og om det drejede sig om et dyr, eller om det kunne være et menneske.", "still",
   "A man in a long dark raincoat with the hood pulled up over his head, seen from directly behind, standing still in the "
   "rain at the edge of the lantern light among beech trunks, looking toward the low tarpaulin shelter a few metres ahead of "
   "him; the tarpaulin is taut and nothing runs off it; a hurricane lantern hangs from its ridge pole; his hands are in his "
   "pockets; no face visible.",
   move=PUSH(1.08, .5, .45), fx=dict(rain=.6, flicker=.5), ref="t16"),
 S("t07", 374.5, 385.5, "Så det var det, vi stod med til at begynde med. Og så drejede det sig om forsigtigt at løsne noget af det …", "still",
   "Close-up of a hurricane lantern hanging from a wooden tarpaulin pole at night, its warm flame glowing, raindrops falling "
   "through its light, the dark tarpaulin above, blurred wet beech trunks behind.",
   move=PUSH(1.07, .5, .45), fx=dict(rain=.8, flicker=1.0)),
 S("t08", 385.5, 395.2, "…det forbrændte stof … forsigtigt at løfte det op, nogle flige.", "still",
   "An open, battered aluminium medical case resting on a wooden folding stool on wet leaves under the tarpaulin: long "
   "forceps, scissors, a torch and plain unmarked brown paper bags lying still inside it, lantern light on the metal, "
   "raindrops on the lid; no people, no hands.",
   move=dict(a=(.46, .5, 1.10), b=(.54, .5, 1.10)), fx=dict(flicker=.3)),
 S("t09", 395.2, 413.5, "Og så kunne jeg se noget, der så ud som menneskehud, som var varmepåvirket …", "still",
   "High wide view through wet black branches at night: deep in a hollow among dark beech trunks, the small tarpaulin "
   "shelter glowing warm like a lantern, three tiny figures standing still around it, mist and rain filling the forest.",
   move=PULL(1.12, .5, .56), fx=dict(rain=.7, flicker=.3), ref="s49"),
 S("t10", 413.5, 429.3, "…det drejede sig ikke om et får eller et svin … men om et menneske. Og meget mere kunne vi ikke sige.", "still",
   "A police officer in a dark 1990s Danish police raincoat and peaked cap, seen from behind, standing still on a forest "
   "track at a cordon of plain red-and-white striped tape tied between two beech trunks, a police car further back with a "
   "blue light on its roof, rain.",
   move=PUSH(1.07, .5, .48), fx=dict(rain=.7, blue=1.0)),
 S("t11", 429.3, 437.3, "Fordi det vigtige var at få denne bylt over til Retsmedicinsk Institut …", "still",
   "The same battered aluminium medical case, now closed with its latches shut, resting on the wooden folding stool on wet "
   "leaves under the tarpaulin, lantern light on the lid, raindrops on the metal; no people.",
   move=PUSH(1.06), fx=dict(flicker=.3), ref="t08"),
 S("t12", 437.3, 454.05, "…uden at vi begyndte at pille for meget ved det … stille og roligt på Retsmedicinsk Institut.", "still",
   "A quiet, empty 1990s hospital basement corridor at night: white tiled walls, a closed pair of grey double swing doors "
   "at the far end, one ceiling lamp lit above them, a wet floor reflecting the light, rain on a small high window; nothing "
   "else in the corridor; no people.",
   move=PUSH(1.09, .5, .5), fx=dict(rain=0, flicker=0), audio="int"),
 S("t13", 454.05, 462.85, "I kriminalteknisk afdeling fik de også travlt, husker kriminaltekniker Bent Hyttholm Jensen.", "still",
   "A 1990s police forensic department office at night: a grey metal desk with a green-shaded desk lamp switched on, a "
   "closed aluminium case and stacks of plain grey folders on the desk, a raincoat on a hook by the door, a dark window with "
   "rain; no people.",
   move=dict(a=(.45, .5, 1.10), b=(.55, .5, 1.10)), audio="int"),
 S("t14", 462.85, 471.0, "…så jeg kørte selvfølgelig derned, for at se, hvad der foregik.", "map",
   move=dict(view="region_drive")),
 S("t15", 471.0, 483.3, "…man havde fundet noget, der lignede et bål nede i bunden af en kløft …", "still",
   "From the upper edge of a steep wooded ravine at night, looking down between two big beech trunks: a wet slope of roots, "
   "mud and fallen beech leaves, and far below at the bottom the small tarpaulin shelter glowing with lantern light; rain; "
   "no people.",
   move=dict(a=(.5, .40, 1.10), b=(.5, .60, 1.10)), fx=dict(rain=.7, flicker=.3), ref="s49"),
 S("t16", 483.3, 494.0, "…Beredskabsstyrelsen havde dækket over med presenninger. Fordi det styrtede ned med regn.", "still",
   "The dark tarpaulin shelter on wooden poles over the hollow, seen from the side at night in heavy rain, a hurricane lantern "
   "hanging under it from the ridge pole, lighting the wet ground beneath, dark beech trunks behind; no people.",
   # was 'ambient': Veo's water streams looked like a scrolling solid texture (judge, 2026-09-28)
   move=PUSH(1.06, .5, .5), fx=dict(rain=1.0, flicker=.4,
       dry=[[(.44, .36), (.58, .30), (.70, .45), (.80, .85), (.45, .85), (.42, .60)]]), ref="s48"),
 S("t17", 494.0, 506.1, "…så sikrede man selvfølgelig afdøde, og der var man meget opfindsom …", "still",
   "A 1990s Danish rescue-service truck without any lettering parked on a muddy forest track at night, its rear roller door "
   "open showing stacked grey equipment boxes, a blue light on the cab roof, three large plain plywood boards leaning "
   "against its side, rain; nobody visible.",
   move=PUSH(1.07, .48, .5), fx=dict(rain=.8, blue=.8)),
 S("t18", 506.1, 514.5, "Liget var pakket ind i plastik … for at bringe det ind så intakt som overhovedet muligt,", "still",
   "Two large sheets of raw plywood lying flat side by side on the wet forest floor, a folded roll of clear plastic sheeting "
   "lying beside them, raindrops beaded on the wood, lantern light from the side; nothing on the boards; no people.",
   move=PUSH(1.06, .5, .5), fx=dict(rain=.5), mono=False),
 S("t19", 514.5, 524.55, "…fik lagt liget op på den her spånplade, så op i ligvognen, og så blev den kørt ind på Retsmedicinsk Institut,", "still",
   "A plain dark 1990s estate hearse without any lettering parked on a muddy forest track at night, seen from behind, its "
   "rear door closed, red-orange tail lights glowing, rain falling through the light, the warm glow of the tarpaulin shelter "
   "far behind among the trees; no lanterns in the trees; nobody visible.",
   move=PULL(1.10, .5, .52), fx=dict(rain=.8)),
 S("t20", 524.55, 535.0, "…På Frederik V's Vej på Østerbro i København ligger Retsmedicinsk Institut i Teilum-bygningen lige ved siden af Rigshospitalet.", "map",
   move=dict(view="zoom_institute")),
 S("t21", 535.0, 541.5, "Her stod retsmediciner Hans Petter Hougen klar til at tage imod liget i den sektionsstue, de kalder drabsstuen.", "still",
   "An empty 1990s autopsy room at night: white tiled walls, a stainless steel autopsy table in the centre under a large "
   "round surgical lamp switched on, a drain in the tiled floor, a steel instrument trolley covered with a green cloth, "
   "everything clean and waiting; no people.",
   move=PUSH(1.08, .5, .5), audio="int"),
]
TAIL = 2.5   # picture and room tone hold after the last word, then fade to black

out = []
for s in SHOTS:
    if s["kind"] != "map":
        s["image_prompt"] = s["image"] + (MONO_TXT if s["mono"] else "") + (STILL_TXT if s["kind"] == "still" else "") + " " + STYLE
    if s["kind"] == "ambient":
        s["motion_prompt"] = MOTION + s["motion"]
        s["negative"] = NEG
    out.append(s)
assert all(abs(a["end"] - b["start"]) < 1e-6 for a, b in zip(out, out[1:])), "shots must butt"
json.dump({"start": out[0]["start"], "end": out[-1]["end"], "tail": TAIL, "fps": 24, "shots": out},
          open("sec2/shots.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "shots,", round(out[-1]["end"] - out[0]["start"], 1), "s, avg",
      round((out[-1]["end"] - out[0]["start"]) / len(out), 1), "s;",
      sum(s["kind"] == "ambient" for s in out), "ambient,", sum(s["kind"] == "map" for s in out), "maps")
