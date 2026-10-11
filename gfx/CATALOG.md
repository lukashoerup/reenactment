# Method E — shot catalogue (the authoring contract)

A scene is a JSON file in `episodes/<ep>/scenes/`. It is written from the transcript,
by a person or by Claude, and checked by `python3 -m gfx.render <scene> --lint` before any
frame is rendered. Everything a viewer reads must be said in the episode or be in
`case.json` with the timecode where it is said.

## Scene file

```json
{
 "id": "S1-fundet", "title": "…", "note": "why this scene, which of Lasse's timecodes",
 "audio": {"from": "02:59.30", "to": "05:27.40"},     // episode clock; narration is never edited
 "bed": "rain" | "none", "bed_db": -31,                // quiet ambience under the voice
 "rain": 0.55,                                         // default rain overlay for every shot (0–1)
 "shots": [ {shot}, … ]                                // in order; a shot ends where the next starts
}
```

## Shot

```json
{"id": "5", "type": "map",
 "at": {"word": "Politiet bliver tilkaldt", "near": "03:31.0", "offset": -0.15},
 "transition": "cut" | "fade:0.5" | "dip:0.6",         // into this shot
 "fade_in": 0.5, "fade_out": 0.4,                      // from/to black inside the shot
 "rain": 0.0–1.0,
 "lt": {"who": "isager", "at": …, "until": …, "top": false},   // lower third: who is speaking
 "credit": "…",                                        // overrides the automatic source line
 "note": "anything a reviewer should know",
 "p": { template parameters }}
```

### Time, everywhere

| Form | Means |
|---|---|
| `"03:41.5"` | episode time |
| `{"word": "Køge", "near": "03:18", "offset": -0.2, "edge": "start"/"end"}` | the spoken word nearest `near` (spelling slips tolerated) |
| `2.5` (inside `p`) | seconds after the shot starts; `-1` = already there when the shot starts |

Keys that take a time: `at`, `until`, `out`, `label_at`, `sub_at`, `who_at`, `draw_until`, `words_until`.
Cut slightly **before** the line (`offset` −0.1 to −0.3); make things appear a beat before
the word (`offset` −0.3 to −0.6) so the eye arrives as the ear does.

### References into case.json

`"@koege"` → a place's [lon, lat] · `"@route:kbh-koege"` → road route coordinates ·
`"@site:road"` → the schematic site layout (metres) · lower thirds and quotes take
`"who"`/`"speaker"` = a key in `case.people`. Fix a fact once in case.json, every scene follows.

## Templates

| type | for | key parameters |
|---|---|---|
| `map` | where: real geography, routes, distances, zones | `cam:[{at, center, zoom, bearing, ease, path:"fly"/"linear"}]`, `places:[{name, ll, cls:"big"/"sea", at, until}]`, `markers:[{ll, kind:"dot"/"ember", label, sub, side:"right"/"left"/"up"/"down", leader, at, until}]`, `routes:[{coords, color, width, dash, at, until, out, head, label}]`, `rings:[{center, radius (m), fill, dash, label, at, until}]`, `areas:[{coords, at}]`, `sat:[{at, v}]` (aerial opacity), `caption:{k, h, s, at, until}` |
| `siteplan` | what happened on the spot, top-down, in metres | `extent`, `cam:[{at, x, y, zoom (px/m), rot}]`, `items:[trees, road, path, tracks, steps, fire, ring, zone, scatter]` each with `at`, `until`, `draw` (seconds) or `draw_until`, `label`, `sub`, `lx/ly`, `lalign`; `words:[{text, x, y, at}]`, `caption`, `credit` ("Skitse, ikke målfast") |
| `facts` | findings and reasoning | `heading`, `layout:"list"` (newest in focus) or `"chain"` (A → B → conclusion), `items:[{text, sub, hot, at}]` |
| `quote` | the speaker's own words, lighting up as spoken | `text` (correct Danish), `from`/`to` (window to align against), `speaker` or `who`/`role`, `hl:[phrases in ember]` |
| `title` | time/place stamps, one big statement | `kicker`, `lines:[…]`, `sub`, `size`, `pos:"lower-left"/"center"`, `at`, `hot` |
| `card` | chapter cards (numbered: a real sequence) | `num`, `title`, `sub` |
| `timeline` | dated events | `events:[{when, label, sub, at, hot}]`, `gap`, `focus` |
| `photo` | a real photograph with its credit | `src` (in the episode folder), `credit`, `from/to:{x, y, s}`, `caption` |
| `object` | an object modelled in code (bottle, plaster cast) | `model:"bottle"/"cast"`, `orbit:[{at, az, el, dist}]`, `shift`, `flicker`, `caption`; credit must say it is a model |
| `diorama` | the find site in 3D: forest clearing, bonfire, road, rain, faceless figures (Fern-style re-usable set); `look:"v3"` finishing pass by default | `site:"@site"`, `cam:[{at, pos:[x,h,y], look:[x,h,y], fov}]` (spline through all keys), `fire`/`smoke:[{at, v}]` (0 = out; a fire at 0 for the whole shot is drawn burnt-out), `light:"overcast"/"night"`, `fog`, `items:[label, text3d, steps, tracks, ring, markers, tape, tarp, litter, car, bottle]`, `caption`; credit defaults to "Model af fundstedet, ikke målfast" |

### People in the diorama (faceless figures, Fern style)
`{"type": "figure", "cast": "@cast:child_red", ...}`. The cast lives in `case.json` → `cast`
(height, colours, hood), so a person looks the same in every shot. A figure has no face,
hair or likeness; posture and action carry the story.
- Standing: `pos:[x, y]`, `pose` (`stand`, `look_down`, `point`, `crouch`, `kneel`, `hold`),
  `look_at:[x, y]` or `face` (degrees), timed changes `poses:[{at, pose}]`.
- Moving: `moves:[{path:[[x, y], …], at, until, gait:"walk"/"run"}]`; between and after
  moves the figure stands at the end of the last path, facing `look_at`.
- `at` / `until` / `fade_in` / `fade_out` show and hide it.
- Frame backs, profiles and silhouettes; never a blank face filling the frame.

### Diorama camera rules
Trees stand everywhere except the clearing (13 m around the fire), the road (3.4 m) and the
path. Keep the camera inside the clearing (< 9 m from the fire), on the road at eye height
(1.5–2 m, a couple of metres to the side if a car will pass), or above 25 m. Anywhere else
the lens ends up inside a tree crown. `text3d` scales with distance (`ref` = the distance
at which it has its set size); one statement at a time reads best (`until` = next `at`).

## House rules (also in docs/PROJECT.md)

- Never a body, an injury or a face. People appear as faceless figures (2026-10-11). Injury details stay in the audio.
- No echo: on-screen text adds names, places, numbers or the one key statement; it never repeats the narration (`--lint` warns; `echo_ok:true` marks a deliberate exception).
- A schematic is labelled as one ("Skitse, ikke målfast"); a model is labelled as one.
- No invented precision: an unnamed place is a dashed zone, not a pin.
- Unclear words in the transcript are not put on screen — use a breather shot instead.
- Name a speaker only when the episode names them and the spelling is checked.
- Readable text is allowed (decision 2026-10-11) but must be designed graphics, never a
  fake document, newspaper page or police record (rule 3 still holds).
- Average shot 6–12 s is fine for graphics if something changes inside the shot.
- Prefer showing over listing: a finding belongs on the place it is about (a label in the
  diorama, a ring on the ground) or as one statement in space. `facts` lists are a last resort.
- The day of the find is "en regnvejrsdag": the diorama defaults to overcast rain, not night.

## Workflow for a full episode

1. `python3 transcribe.py --all` (≈ 45–60 min CPU, resumable).
2. Fill `case.json`: people, places (`python3 -m gfx.geo case.json`), facts with timecodes, site layout.
3. Split the episode into scenes of 1–4 minutes at natural turns; write each scene file
   (Claude can draft from the transcript + this catalogue).
4. `--lint` each scene; fix every error, read every warning.
5. `--preview` render (720p), review the contact sheet and the web copy; adjust.
6. Final render (1080p). Shots are cached by content: only changed shots re-render.
