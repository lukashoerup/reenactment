"""Section 1 of Danske Drabssager "Det Brændende Lig": 0:00–5:06.3, drawn style (C), one version.
Times are on the episode clock (seconds). Writes sec1/shots.json.

kind: new   -> keyframe (drawn) + video on Google Cloud (no children possible there)
      reuse -> an existing drawn clip (children shots from the cold-open test)
pin:  True  -> first frame = last frame (static shot; stops invented events)
ref:  id of another new shot whose keyframe must be matched (place / object continuity)
"""
import json

STYLE = ("Hand-made documentary illustration: charcoal and black ink wash on warm grey paper, loose confident "
         "strokes, visible paper grain and smudges, mostly monochrome grey and black. The only colour is warm "
         "orange-yellow soft pastel for light sources (fire, lamps, headlights, lit windows); emergency lights may "
         "use one muted blue pastel. Reportage-sketch look like a courtroom sketch artist: not digital painting, "
         "not anime, not a comic. Denmark, late September 1999. No readable text, letters or numbers anywhere, "
         "no logos. No faces: people only from behind, in silhouette, or as hands. 16:9 composition.")
MOTION = ("Animated hand-drawn charcoal and ink illustration: every frame keeps exactly the same drawn style, "
          "paper texture and pastel colours as the image; it never turns photographic or cartoonish. "
          "Subtle, restrained, slow motion like a documentary drawing brought to life. ")
STILL = "Static shot, the camera remains completely still. Nothing and nobody enters the frame. "
NEG = ("thrown object, flying object, falling log, stick, extra person, face, crowd, text, letters, numbers, logo, "
       "cartoon, anime, photograph, camera shake, music, speech")

def S(id, a, b, line, img="", mot="", pin=False, dur=4, ref=None, reuse=None, rin=0.0, audio="rain"):
    return dict(id=id, start=a, end=b, line=line, kind="reuse" if reuse else "new", image=img, motion=mot,
                pin=pin, dur=dur, ref=ref, reuse=reuse, rin=rin, audio=audio)

SHOTS = [
 # ---- teaser: the pathologist's line, then the forest -------------------------------------------------
 S("s01", 0.0, 6.5, "(music) Hun havde ikke trukket vejret under ilden.",
   "Extreme close-up of dying embers in wet grey ash at night, a few embers still glowing orange, one thin line of smoke rising straight up in still air, raindrops on the ash.",
   STILL + "The embers pulse faintly, the thin smoke rises straight up, raindrops hiss on the ash. Audio: soft rain, faint hiss of embers.", pin=True, dur=8),
 S("s02", 6.5, 13.0, "Det vil sige, at hun var død, da hun blev lagt på bål.",
   "A microscope on a laboratory bench under a single warm desk lamp, a rack of glass slides beside it, dark room, 1990s forensic laboratory.",
   "Very slow push-in toward the microscope. Only the camera moves. Audio: quiet room tone, a ventilation hum.", dur=8, audio="room"),
 S("s03", 13.0, 20.4, "(music)",
   "Wide view of a beech forest at dusk in heavy rain, tall grey trunks fading into mist, a muddy track leading into the trees.",
   "Slow sideways drift of the camera. Rain falls steadily, mist moves slightly between the trunks. Audio: heavy rain on leaves.", dur=8),
 S("s04", 20.4, 25.0, "To børn fik deres livs chok, og leg blev vendt til gru,",
   "A child's small bicycle lying on its side on a wet forest track, front wheel off the ground, beech leaves in puddles, rain; no people.",
   STILL + "The raised front wheel turns slowly and comes to rest; rain falls into the puddles. Audio: rain, a faint tick of the wheel.", dur=6),
 S("s05", 25.0, 29.4, "da de i et bål fandt en bylt, som indeholdt de jordiske rester af et menneske.",
   "Seen from a distance through wet beech trunks: a large bonfire burning in a shallow hollow in heavy rain, a dark shapeless bundle of blankets in its middle; no people.",
   STILL + "Flames flicker and lean, rain falls through the firelight, smoke drifts. Audio: rain, distant crackle of fire.", pin=True, dur=6, audio="fire"),
 S("s06", 29.4, 34.5, "Ugenkendelig, dræbt, forbrændt og efterladt.",
   "Grey morning: the burned-out bonfire, a circle of wet black ash and charred branches in the hollow, rain, empty forest around it; no people.",
   STILL + "Rain falls on the ash, a few wisps of steam rise. Audio: steady rain.", pin=True, dur=6, ref="s05"),
 S("s07", 34.5, 39.3, "Det blev starten på den drabsefterforskning, som du kommer til at høre om…",
   "Close-up: a new brown cardboard case folder tied with string lying on a grey metal office desk under a warm desk lamp, rain-streaked window behind.",
   STILL + "The lamp light is steady; rain runs down the window behind. Audio: office room tone, rain on the window.", pin=True, dur=6, audio="room"),
 S("s08", 39.3, 47.2, "Sagen var en efterforskningsmæssig spændende sag, hvor eksperter … arbejdede sammen.",
   "A long 1990s police headquarters corridor with fluorescent ceiling lights and linoleum floor; two figures seen from behind walk away carrying folders.",
   "The two figures walk slowly away down the corridor; one ceiling light flickers once. Camera still. Audio: footsteps, room tone.", dur=8, audio="room"),
 S("s09", 47.2, 49.3, "Kriminalteknikere, retsantropologer,",
   "Close-up of an open aluminium crime-scene kit on a table: fingerprint brushes, powder jars, paper evidence bags, a gloved hand resting beside it.",
   STILL + "The gloved hand lifts a brush slightly. Audio: faint clink.", dur=4, audio="room"),
 S("s10", 49.3, 51.2, "retsodontologer,",
   "Close-up of a steel tray with a dental mirror and dental probe beside blank dental chart cards, clinical lamp light.",
   STILL + "Only the lamp light shimmers faintly on the steel. Audio: room tone.", pin=True, dur=4, audio="room"),
 S("s11", 51.2, 53.0, "drabsefterforskere,",
   "A wall of pinned papers, maps and turned-over photographs with string between pins, seen at an angle in a dim office.",
   STILL + "Slow push-in; the papers stay still. Audio: room tone.", dur=4, audio="room"),
 S("s12", 53.0, 54.9, "retsmedicinere og jurister.",
   "An empty Danish courtroom: rows of light wooden benches, tall windows with grey daylight, a raised judges' table; no people.",
   STILL + "Dust drifts in the window light. Audio: large quiet room.", pin=True, dur=4, audio="room"),
 S("s13", 54.9, 58.9, "Vi hører om en tom flaske tændvæske efterladt i et bål,",
   "Close-up: a small plastic lighter-fluid bottle, melted and blackened on one side, half sunk in grey ash among charred twigs; no label.",
   STILL + "Faint heat shimmer above the ash, a raindrop lands. Audio: rain on ash.", pin=True, dur=4, ref="s06"),
 S("s14", 58.9, 61.3, "et dækspor i skovbunden",
   "Close-up of a single car tyre track pressed into soft mud at the edge of a forest track, rainwater standing in the tread pattern.",
   STILL + "Raindrops ripple the water in the tread. Audio: rain.", pin=True, dur=4),
 S("s15", 61.3, 65.6, "og et billede i avisen af en afdød kvindes maltrakterede ansigt",
   "Dawn: a bundle of tabloid newspapers tied with string lying face down on a wet pavement outside a closed kiosk with its shutter down; no readable print.",
   STILL + "Rain falls on the bundle and the pavement. Audio: city rain, a distant car.", pin=True, dur=6, audio="city"),
 S("s16", 65.6, 69.8, "og om beslutninger, der skal træffes, selv om de kan virke brutale.",
   "Close-up of a man's hand resting next to a beige 1990s desk telephone on a grey metal desk, lamp light, the receiver still on the hook.",
   STILL + "The hand lifts slightly and hesitates above the receiver, then stops. Audio: room tone, rain on window.", dur=6, ref="s07", audio="room"),
 S("s17", 69.8, 75.5, "…tidligere drabschef Bent Isak Nielsen,",
   "An empty office chair behind a grey metal desk, a grey suit jacket hanging over its back, venetian blinds with rainy daylight, stacks of case folders.",
   STILL + "Rain shadows move slowly on the blinds. Audio: office room tone, rain.", pin=True, dur=6, ref="s07", audio="room"),
 S("s18", 75.5, 79.0, "kriminaltekniker Bent Hyttholm Jensen,",
   "A white disposable forensic overall with hood hanging on a wall hook next to a 1990s film camera with a flash unit on a shelf.",
   STILL + "Nothing moves except a faint flicker of the ceiling light. Audio: room tone.", pin=True, dur=4, audio="room"),
 S("s19", 79.0, 81.3, "professor i retsmedicin Hans Petter Hougen",
   "A white lab coat hanging on a hook in a tiled hospital corridor, a round operating lamp visible through a doorway behind.",
   STILL + "The light in the doorway hums steadily. Audio: room tone.", pin=True, dur=4, audio="room"),
 S("s20", 81.3, 85.5, "og tidligere anklager Anne Birgitte Stürup. Alle har de haft med sagen at gøre…",
   "A black lawyer's gown on a wooden hanger in a wood-panelled court corridor, tall window with grey light.",
   STILL + "The gown hangs still; dust drifts in the light. Audio: quiet corridor.", pin=True, dur=6, ref="s12", audio="room"),
 S("s21", 85.5, 93.4, "Mit navn er Stine Bolther. Velkommen til podcasten Danske Drabssager…",
   "A podcast studio at night: a microphone with a round pop filter on a desk, headphones beside it, a small red on-air lamp glowing, dark acoustic panels.",
   "Very slow push-in toward the microphone; the on-air lamp glows steadily. Audio: quiet studio room tone.", dur=8, audio="room"),
 S("s22", 93.4, 97.6, "(music)",
   "Beech forest at dusk in heavy rain, a faint orange glow of a fire far away between the trunks; no people.",
   "Slow push forward between the trunks toward the distant glow. Rain falls. Audio: heavy rain.", dur=4, ref="s03"),
 # ---- cold open (children shots reused from the test; fire/bundle redrawn without children) -----------
 S("c1", 97.6, 101.81, "Bålets flammer lokker de nysgerrige børn tættere på.", reuse="clips/S1_C.mp4", rin=0.6),
 S("c2", 101.81, 105.81, "Selvom regnen står ned i stænger, buldrer ilden lystigt.",
   "Medium close view of a large bonfire of branches burning fiercely in a shallow hollow in a beech forest in heavy rain, steam and smoke; no people anywhere.",
   STILL + "Flames roar and twist, rain streaks fall through the firelight, steam rises. Audio: roaring fire, heavy rain.", pin=True, dur=4, ref="s05", audio="fire"),
 S("c3", 105.81, 108.31, "Midt i bålet ligger en bylt.", reuse="clips/S3_C.mp4", rin=1.0),
 S("c4", 108.31, 110.68, "På cirka 70 centimeter.",
   "Extreme close-up of the corner of a red-and-black checked woollen blanket charring at its edge, glowing embers creeping along the weave, wisps of smoke; only fabric texture fills the frame.",
   STILL + "Embers creep slowly along the charring edge of the wool; smoke curls up. Audio: close crackle of embers.", pin=True, dur=4, audio="fire"),
 S("c5", 110.68, 112.6, "Hvad er det?", reuse="clips/S5_C.mp4", rin=0.4),
 S("c6", 112.6, 114.89, "Et dyr?", reuse="clips/S6_C.mp4", rin=1.2),
 S("c7", 114.89, 116.52, "Affald?", reuse="clips/S7_C.mp4", rin=1.4),
 S("c8", 116.52, 118.3, "Eller et menneske?",
   "Close view of tall flames and thick grey smoke filling the whole frame at night in heavy rain; only fire, smoke and rain, no objects, nothing inside the fire is visible.",
   STILL + "The flames rise higher and the smoke thickens; nothing else moves. Audio: fire building, rain.", pin=True, dur=4, audio="fire"),
 S("c9", 118.3, 119.4, "(pause)", img="BLACK"),
 # ---- Retsmedicinsk Institut ---------------------------------------------------------------------------
 S("s23", 119.4, 124.8, "På Retsmedicinsk Institut pakker de forsigtigt det forkullede liv ud.",
   "Night exterior of a 1990s Copenhagen institute building of dark brick, rain, one lit window on the ground floor, wet cobbles.",
   STILL + "Rain falls through the light of the window. Audio: city rain.", pin=True, dur=6, audio="city"),
 S("s24", 124.8, 129.6, "Stykke for stykke trækker de plastik og stof af den døde krop.",
   "Close-up of two hands in surgical gloves folding back the corner of a heavy grey plastic sheet at the edge of a steel table; everything under the sheet is outside the frame.",
   "The gloved hands slowly fold the corner of the plastic back and hold it; nothing beneath is ever visible. Camera still. Audio: rustle of plastic, room hum.", dur=6, audio="room"),
 S("s25", 129.6, 134.6, "Benene er brændt bort, ansigtet stort set væk.",
   "A round operating lamp seen from below, hard white-orange light, tiled wall behind; nothing else in frame.",
   STILL + "The lamp's light hums; a faint flicker. Audio: ventilation hum.", pin=True, dur=6, ref="s19", audio="room"),
 S("s26", 134.6, 140.9, "Er det en kvinde, en mand eller et barn?",
   "A hospital corridor with double swing doors with round windows, light behind the doors, tiled walls; no people.",
   "The double doors swing gently and come to rest; the light behind them is steady. Camera still. Audio: doors settling, room hum.", dur=8, ref="s19", audio="room"),
 # ---- Ekstra Bladet ------------------------------------------------------------------------------------
 S("s27", 140.9, 147.9, "Hvem kender brændt kvinde? Sådan stod der i Ekstra Bladet den 30. september 1999.",
   "Night printing press hall: a broad web of newsprint running fast over large rollers, ink-dark machinery, warm work lamps; no readable print.",
   "The paper web runs fast over the rollers; the machine vibrates. Camera still. Audio: loud rhythmic printing press.", dur=8, audio="press"),
 S("s28", 147.9, 152.2, "Politiet havde valgt at offentliggøre et billede af en dræbt uidentificeret kvinde",
   "Dawn: a closed kiosk on a wet Copenhagen street corner, the newspaper bundle face down on the pavement by the shutter, a delivery van's red tail lights leaving in the distance.",
   "The van's tail lights move away into the rain; everything else is still. Audio: rain, van driving off.", dur=6, ref="s15", audio="city"),
 S("s29", 152.2, 157.0, "i håb om, at nogen vil kunne lede efterforskningen i en rigtig retning.",
   "A 1990s kitchen table in grey morning light: a folded tabloid newspaper lying face down next to a cup of coffee, rain on the window behind; no people.",
   STILL + "Steam rises slowly from the coffee; rain runs down the window. Audio: kitchen room tone, rain.", pin=True, dur=6, audio="room"),
 S("s30", 157.0, 163.8, "Hendes hår var afbrændt, øjnene lukket og munden åbenstående…",
   "Extreme close-up of the folded edge of the face-down newspaper on the table, coarse halftone dots bleeding through the paper, nothing recognisable.",
   STILL + "Very slow push-in on the paper edge; nothing else moves. Audio: rain on the window, a clock ticking.", dur=8, ref="s29", audio="room"),
 # ---- Rejseholdet --------------------------------------------------------------------------------------
 S("s31", 163.8, 171.0, "Bent Isak Nielsen er tidligere drabschef ved Rigspolitiets Rejsehold…",
   "A man of about fifty in a grey suit with short grey hair seen from behind, standing at an office window with venetian blinds, rain outside, grey metal desk behind him.",
   STILL + "The man stands still, breathing slowly; rain runs down the window. Audio: office room tone, rain.", pin=True, dur=8, ref="s17", audio="room"),
 S("s32", 171.0, 177.8, "…han tager os her tilbage til fundet af den dræbte kvinde i en skov nær Køge.",
   "View through a car windscreen driving along a wet Danish country road toward a beech forest at dusk, headlights on, rain on the glass.",
   "The car drives slowly forward; the wipers sweep once across the windscreen. Audio: car interior, wipers, rain.", dur=8, audio="car"),
 # ---- Bent's account -----------------------------------------------------------------------------------
 S("s33", 177.8, 182.0, "Der er nogle børn, der leger, selvom det er regnvejr,",
   "A worn rope swing hanging from a beech branch in the rain, a football lying in the wet leaves beneath it; no people.",
   STILL + "The rope swing sways very slightly; rain falls. Audio: rain on leaves.", dur=6, ref="s03"),
 S("s34", 182.0, 186.2, "…et kæmpe bål med meget høje flammer.",
   "Very tall flames of a big bonfire seen through wet branches from about thirty metres away in heavy rain; no people.",
   STILL + "The tall flames leap and sway; rain falls through the glow. Audio: rain, distant roaring fire.", pin=True, dur=6, ref="s05", audio="fire"),
 S("s35", 186.2, 188.4, "Det virker helt mærkeligt sådan en regnvejrsdag.", reuse="CLIP:c2", rin=0.5),
 S("s36", 188.4, 191.4, "Og de synes, der ligger noget inde i flammerne,", reuse="clips/S7_C.mp4", rin=0.0),
 S("s37", 191.4, 194.6, "…nogle fornuftige børn, som kontakter nogle voksne,",
   "A hallway of a 1990s Danish house: a wall-mounted telephone, a rain jacket on a hook, a front door with a rain-streaked glass pane; an adult man seen from behind lifts the receiver.",
   "The man lifts the receiver to his ear; rain runs down the door glass. Camera still. Audio: house room tone, rain.", dur=4, audio="room"),
 S("s38", 194.6, 198.3, "som slår alarm til politiet, og det er derved Køge Politi.",
   "A 1990s police station radio desk: a radio console with a handheld microphone, a desk lamp, a map on the wall, an officer's hand pressing the microphone button.",
   "The hand presses the microphone button; a small indicator light glows. Audio: radio static, room tone.", dur=4, audio="radio"),
 S("s39", 198.3, 204.2, "Køge Politi rykker ud, og kan man det samme se, at der er et eller andet mærkeligt.",
   "A white 1990s police estate car with a blue light bar stopped on a muddy forest track in heavy rain, headlights on, no markings readable.",
   STILL + "The blue lights rotate and reflect on the wet trunks; rain falls in the headlights. Audio: rain, idling engine.", pin=True, dur=6, audio="rain"),
 S("s40", 204.2, 212.5, "Der ligger et … formentlig mennesker, men det er et arrangeret bål. Politiet bliver tilkaldt.",
   "Two police officers in dark 1990s Danish uniforms and caps seen from behind at the edge of a smoking bonfire hollow in the rain, one pointing a torch beam at the fire.",
   "The officers stand still; the torch beam trembles slightly on the smoke; rain falls. Audio: rain, hiss of wet fire.", dur=8, ref="s05", audio="fire"),
 # ---- the phone chain ----------------------------------------------------------------------------------
 S("s41", 212.5, 217.1, "…jeg er drabschef i Rejseholdet på det her tidspunkt, og bliver ringet op",
   "Close-up of a beige 1990s desk telephone on a grey metal desk with case folders; a man's hand in a grey suit sleeve reaches in and lifts the receiver.",
   "The hand lifts the receiver off the phone. Camera still. Audio: telephone ring stops, room tone.", dur=4, ref="s16", audio="room"),
 S("s42", 217.1, 223.6, "af kriminalchefen i Køge, som siger, vi har brug for hjælp…",
   "A small 1990s provincial police office at dusk: a man in shirtsleeves seen from behind on the telephone at the window, rain outside, desk lamp on.",
   STILL + "The man stands still holding the phone; rain runs down the window. Audio: room tone, rain.", pin=True, dur=8, audio="room"),
 S("s43", 223.6, 232.3, "…en af mine medarbejdere i Rejseholdet. Han boede privat i Ejby, og ikke ret langt fra stedet.",
   "A rural yellow-brick Danish house at dusk in heavy rain, one warm lit window, a hedge and a gravel drive with a parked car.",
   STILL + "Rain falls; the lit window glows steadily. Audio: rain, distant wind.", pin=True, dur=8),
 S("s44", 232.3, 239.3, "Og ham ringede jeg, eller min daværende chef…",
   "Inside that house: a hallway table with a 1990s telephone ringing, a man seen from behind in a knitted jumper reaching for it, lamp light.",
   "The man picks up the receiver. Camera still. Audio: phone ring stops, room tone.", dur=8, ref="s43", audio="room"),
 S("s45", 239.3, 244.3, "Men i hvert fald, Poul, som han hed, han var også ude at være med til de indledende ting.",
   "The same yellow-brick house at dusk in the rain: a car with headlights on backs out of the gravel drive onto the road.",
   "The car slowly backs out of the drive, its headlights sweeping across the hedge. Audio: car engine, tyres on gravel, rain.", dur=6, ref="s43", audio="car"),
 # ---- emergency services --------------------------------------------------------------------------------
 S("s46", 244.3, 250.9, "…det man konstaterer i den her regnvejrstunge september i 99,",
   "Wide: the beech forest at dusk in heavy rain, blue emergency lights flickering between the trunks from vehicles out of sight, mist.",
   STILL + "Blue light pulses on the wet trunks; rain falls. Audio: heavy rain, distant engines.", pin=True, dur=8, ref="s03", audio="rain"),
 S("s47", 250.9, 257.8, "…man får tilkaldt beredskab og Falck og presenninger for at overdække findestedet,",
   "Three figures in rain gear seen from behind rigging a large tarpaulin on poles over the hollow in the forest, portable work lamps glowing, rain.",
   "The figures pull the tarpaulin taut; the lamps glow; rain drums on the tarp. Audio: rain on tarpaulin, voices far away without words.", dur=8, ref="s05", audio="rain"),
 S("s48", 257.8, 262.4, "Men at sikre spor. Sporene bliver ret vigtige…",
   "Under the tarpaulin: a work lamp lighting the circle of wet ash and charred branches, rain pouring off the tarp edge; no people.",
   STILL + "Rain pours off the tarp edge; the lamp is steady. Audio: rain drumming on the tarp.", pin=True, dur=6, ref="s06"),
 # ---- traces ----------------------------------------------------------------------------------------------
 S("s49", 262.4, 267.2, "Et udendørs gerningssted, det er altid noget, fanden har skabt…",
   "High wide view through wet branches: the lit tarpaulin tent in the dark wet forest, tiny figures around it, mist and rain.",
   STILL + "Rain falls; the tent glows; tiny figures barely move. Audio: rain on leaves.", pin=True, dur=6, ref="s47"),
 S("s50", 267.2, 273.4, "…i modsætning til et indendørs gerningssted, som er mere overskueligt…",
   "An ordinary, tidy 1990s Danish living room at evening: sofa, a lamp on, a coffee table, closed curtains; quiet and orderly; no people.",
   STILL + "Only the lamp light is steady; nothing moves. Audio: quiet room, a clock ticking.", pin=True, dur=8, audio="room"),
 S("s51", 273.4, 277.9, "Så her er spørgsmålet de ydre parametre. Hvor langt skal man gå ud?",
   "Overhead view of a hand-drawn map of a forest on a table with no writing, a hand holding a pencil compass drawing a wide circle around a small cross.",
   "The hand draws the circle with the compass, slowly. Camera still. Audio: pencil on paper, room tone.", dur=6, audio="room"),
 S("s52", 277.9, 286.4, "…det er jo ikke sikkert, at gerningsmanden har efterladt sig spor lige henne ved bålet…",
   "A line of forensic technicians in white overalls seen from behind, bent down searching the wet forest floor step by step, moving away from the lit tarpaulin, rain.",
   "The line of technicians moves slowly forward, searching the ground; rain falls. Audio: rain, footsteps in wet leaves.", dur=8, ref="s47"),
 S("s53", 286.4, 291.6, "…de overvejelser, man står med som efterforskningsleder. Hvad skal man gøre?",
   "The same grey-haired man seen from behind in a raincoat under a black umbrella, standing at the edge of the search area looking into the dark forest, lamp glow behind him.",
   STILL + "Rain drips from the umbrella; he stands still. Audio: rain on umbrella.", pin=True, dur=6, ref="s31"),
 S("s54", 291.6, 293.9, "Sådan en skov, der er fyldt med kondomer, kapsler,",
   "Close-up of rusty bottle caps and a torn foil wrapper in wet mud and beech leaves.",
   STILL + "Raindrops land on the leaves. Audio: rain.", pin=True, dur=4),
 S("s55", 293.9, 295.6, "plastikposer,",
   "Close-up of a torn plastic bag snagged on a low branch in the rain.",
   STILL + "The plastic bag flutters in the wind; rain falls. Audio: rain, wind.", dur=4),
 S("s56", 295.6, 297.4, "sodavandsflasker,",
   "Close-up of an old glass soda bottle half-buried in wet leaves and moss, no label.",
   STILL + "Rain drips on the glass. Audio: rain.", pin=True, dur=4),
 S("s57", 297.4, 299.2, "skrald, cigaretskodder",
   "Close-up of cigarette butts and a crushed cigarette packet without any print in wet leaves.",
   STILL + "Raindrops land around them. Audio: rain.", pin=True, dur=4),
 S("s58", 299.2, 301.2, "og alt muligt.",
   "Wider view of the forest floor strewn with small rubbish among leaves and roots, rain.",
   STILL + "Rain falls on the leaves. Audio: rain.", pin=True, dur=4),
 S("s59", 301.2, 306.3, "Og hver og en af de ting kan jo teoretisk set være noget, der kommer fra gerningsmanden.",
   "Close-up of a gloved hand holding tweezers lifting a cigarette butt from wet leaves toward a small blank paper evidence bag.",
   "The gloved hand slowly lifts the cigarette butt and drops it into the paper bag. Camera still. Audio: rain, rustle of paper.", dur=6),
]

MONO = {"s03","s04","s06","s12","s13","s14","s15","s20","s29","s30","s33","s54","s55","s56","s57","s58","s59","s46"}
MONO_TXT = (" This image has no warm light source: keep it entirely monochrome grey and black, with no orange at all"
            " (except where the description names a light).")
out = []
for s in SHOTS:
    if s["kind"] == "new" and s["image"] not in ("", "BLACK"):
        s["image_prompt"] = s["image"] + (MONO_TXT if s["id"] in MONO else "") + " " + STYLE
        s["motion_prompt"] = MOTION + s["motion"]
        s["negative"] = NEG
    out.append(s)
json.dump({"end": 306.3, "fps": 24, "shots": out}, open("sec1/shots.json", "w"), ensure_ascii=False, indent=1)
new = [s for s in out if s["kind"] == "new" and s["image"] not in ("", "BLACK")]
print(len(out), "shots,", len(new), "new,", sum(s["dur"] for s in new), "s of video per take")
gaps = [(a["id"], b["id"]) for a, b in zip(out, out[1:]) if abs(a["end"] - b["start"]) > 0.01]
print("gaps/overlaps:", gaps or "none", "| first", out[0]["start"], "last", out[-1]["end"])
