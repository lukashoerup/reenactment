# Learnings — dated, can expire

## 2026-08-20 — Mood stills are not re-enactment
The first test showed places and objects, never people acting. Lukas: "it should have
been a re-enactment". A re-enactment needs someone *doing* something — from behind, as
hands, feet or silhouettes is fine, but the action must be performed.

## 2026-09-27 — The video model invents events for any object verb
Three shots had motion no director would ask for: a log flies into the fire from
off-screen (A1 S2), a stick pokes the bundle from outside the frame (A1 S4), and a log
swings in and lands (S6). The S6 one was caused by **our** prompt ("a branch collapses in
the fire") — the model turned "collapses" into a throw. Each implies a third person in a
scene where nobody else is present. Rule: describe only camera movement and ambient
motion (flames, rain, steam); never ask an object to move unless the cause is visible;
for static shots say "Nothing and nobody enters the frame: no hands, no sticks, no logs
thrown in". Veo Lite has no `negativePrompt`, so this must be in the prompt text.

## 2026-09-27 — Independently generated shots drift apart
Boots red in S1 → green in S6; the smaller child the same height as the older one in S6;
the bundle a charred plaid heap in S4 and a fibrous, body-like mass in S8 — which also
broke the no-body rule on "Eller et menneske?". Fixes that worked for free: make later
shots of the same object from a **crop of the earlier keyframe** (A2 S8 = 1.45× crop of
S4), and cut both shots from one take. Proper fix: a continuity bible (see RESEARCH).

## 2026-09-27 — Pareidolia in textures
The back of the navy hood had dimples forming two eyes and a mouth (S3). A feathered
ellipse blur in the edit removed it (the hoods are foreground and soft anyway). The fire
lump in S3 can read as a head from behind — not fixable without a new take.

## 2026-09-27 — Safety filters: describe the picture, not the story
"True-crime documentary… bundle… children" → blocked (`OTHER`, then `IMAGE_SAFETY`).
"Film still… two children seen from behind… a dark bundle of old woollen blankets" →
passed. Veo accepted children seen from behind with `personGeneration: allow_adult`.

## 2026-09-27 — Edit mechanics that silently hurt
- Trimming by seconds drifted picture 3 frames (0.13 s) late by the end → cut on frames.
- ffmpeg `blend` in YUV gave a purple cast → convert to `gbrp` first.
- Veo clips often start with 0.1 s of near-silence → audible holes at cuts → put a
  continuous ambience bed under the whole scene.
- Luma ranged 19–52 across shots in A1; per-shot brightness trims brought it to 28–36.

## 2026-09-27 — An AI judge works, but is stochastic and only as good as its brief
- Gemini 3.1 Pro, blind, 6 fps: found 6 of 7 content defects Claude had found by eye
  (thrown log, stick, hood face, body-like bundle, falling sparks, fire scale), in 37 s,
  < 1 kr. Gemini 3.5 Flash found only the 2 grossest.
- Missed: boot colour and height continuity; everything measurable (drift, exposure,
  audio holes) → keep code checks.
- Same judge on the fixed cut found new issues that were also in A1 (walk, hands) and
  made one false claim (said the plaid was missing). Run it several times / pairwise.
- **The loop's first run made things worse:** the bundle reference image was sent with
  S2 (a shot before the bundle is revealed), the judge failed S2 for lacking the bundle,
  and its "fix" was fed into the next prompt — which then put a plaid bundle in the fire.
  One brief and one reference set per shot.
- A new S8 take scored 4/10 ("smooth flames, slight melting") yet was clearly better
  than the incumbent (which broke a rule). Judge against the best alternative, not a
  fixed threshold.

## 2026-09-27 — Quota and billing
- Gemini API: after 10 Veo Lite videos the project got `429 exceeded your current quota`
  for hours; Veo Fast still worked. Text models unaffected. Treat it as a daily cap per
  model on a young project (see COST/RESEARCH: Vertex AI, tier upgrades).
- Danish credit balance moved by list price × 1.25 (VAT): our estimate $8.3 ≈ 53 kr
  showed up as ≈ 67 kr.

## 2026-09-27 — Blender on a 2-core CPU looks like a game
Procedural cylinder trees, doll children, stock fire that lights nothing, 10 samples:
1.5 h render, "computer game with dolls". Not a Blender problem — no scanned assets,
no mocap, no GPU, no artist hours. Blender's place: layout/previz, maps and routes,
forensic-style reconstructions, stylised looks, or as control passes for an AI render.

## 2026-09-27 — Styles, as judged by Lukas and by the defects
- A (photo): most gripping, most AI failure modes visible.
- B (stills + camera move): cannot invent motion; nobody performs.
- C (drawn): Lukas's favourite; forgiving of anomalies; Veo Lite still added cartoon
  swirls in the fire, walked a child out of frame, put figures behind the fire.
- D (Blender): see above.

## 2026-09-27 — Google Cloud (Vertex AI) blocks children; the Gemini API did not
New Google Cloud trial project (gmail account; Google auto-created an organization
`lukasbaddie-org`, so the security baseline blocked service-account keys until the
two key-creation policies were overridden on the project). On Vertex, Veo 3.1 Fast
refused both takes of S6 (children's legs and boots only) with support codes 58061214
and 17301594 = child-related content, which needs `personGeneration: allow_all` —
allowlist-only (Google points to sales). The Gemini API had accepted the same
children seen from behind with `allow_adult`. Consequence: shots with children stay on
the Gemini API (paid, 10/day) or another provider; everything else can use Vertex.

## 2026-09-27 — Vertex Veo: what works
- `enhancePrompt: false` is rejected for Veo 3 ("prompt enhancement cannot be
  disabled") — the rewriter is always on.
- `sampleCount: 2` returns two takes per request; blocked takes are not charged.
- **Pinning first and last frame to the same keyframe works**: S2 (fire, rain) came
  back as two clean static takes — no thrown log, no smoke burst — with noun negatives
  ("thrown object, falling log, flying wood, stick, hand, person, smoke burst").
- Videos come back inline (`bytesBase64Encoded`) when no `storageUri` is given.

## 2026-09-27 — Section 1 (5 minutes, drawn) at scale: what broke and what held
- **Trial quotas, not money, set the pace.** A new trial project allowed ≈ 1 image/min
  on gemini-3-pro-image and a few Pro judge calls/min; parallel runs got 429 storms.
  Fixes: 2 workers, backoff up to 120 s, `gemini-3.1-flash-image` (own quota; holds the
  drawn style well enough) for the tail, and `gemini-2.5-pro` as a second judge quota.
- **A judge 429 was counted as a pass** (the fallback returned `pass: True`). Now it
  returns `pass: None` + "UNJUDGED" and those picks are re-judged. Never default a gate
  to "pass" on an error.
- **Keyframe gate earns its cost** ($2 for ~100 checks): it caught extra people in 10
  drawings (a figure on a driveway, two men for one), a body-like heap in the fire (c8
  took five redraws), a skull-like shape in ash, readable text on an evidence bag / map /
  bottle. It is stochastic: 5 drawings kept failing on trivia (keypad digits) and were
  kept by hand.
- **Style references must be content-neutral.** Using a keyframe that contained the
  bundle as a style reference put bundles into unrelated shots. Style refs now: the
  fire (kfC/S2) and an empty forest (sec1/kf/s03).
- **Veo draws rain badly in this style**: in c2 and s06 all four takes had rain streaks
  that blink on/off, or no rain. Plan: rain as a real overlay in post.
- **Veo adds colour and sound nobody asked for**: a red smear on the grey newspaper (s30,
  fixed with `hue=s=0` in post), police radio (s42), a phone that keeps ringing after
  pick-up (s41), typing sounds. Next run: `generateAudio: false`, all sound in post.
- "Recitation check failed" on one Veo request (s50): regenerate; nothing to fix.
- **Pinned static shots (first = last frame) were the most reliable class**: no thrown
  objects, no invented entrances. Motion shots needed the judge.
- Ops: long jobs run in the background (`setsid nohup … &`) and are polled — tool calls
  time out at 10 min. `pkill -f <pattern>` also matches the calling shell; kill by PID.
  Never "probe" Veo with an empty prompt: it submits a billable job.
- Artifact delivery: a 180 MB, 5-minute MP4 cannot be attached (15 MB per file, 64 MB per
  publish, only mp4/txt/json/… served). Worked: HLS with fMP4 segments named `.mp4`
  (`-hls_segment_type fmp4`), playlist renamed `.txt`, hls.js 1.5.20 from cdnjs, two
  publishes (≈ 52 + 33 MB).

## 2026-09-28 — Section 2 (5:06–9:02): slower, subtler, real maps — and no video model at all
- **Long shots with motion added in post work.** 21 shots, average 11 s (section 1: 4.6 s). Motion
  toolkit, all free and deterministic (`sec2/move.py`): sub-pixel camera (log zoom + gentle ease,
  cv2.warpAffine), rain streaks re-drawn 12×/s in screen space (hand-animation "on twos"), brighter
  where the drawing is lit, slightly slow; orange light sources breathe a few percent; blue beacon
  pulses. The whole-cut judge: "pacing much improved… fits the sombre tone".
- **Every Veo attempt failed in this style** and was replaced by a still: raindrops became cartoon
  teardrops and white splash stars (t05), water streams off a tarp looked like a scrolling texture
  (t16), smoke "morphs and bubbles" (t02, passed the per-shot judge, failed the whole-cut judge).
  Result: 0 generated motion in the final cut.
- **Stills must not show what only looks right moving**: a drawn waterfall or flame reads as frozen.
  Prompt rule (`STILL_TXT`) + gate rule added. The image model still insists on water pouring off
  tarpaulins — t06 needed a new composition (tarp taut, man from directly behind).
- **Procedural rain needs roofs**: overlay rain "falls through" a tarpaulin (judge: blocker). Fix:
  per-shot `dry` polygons in keyframe coordinates, warped with the camera. Drawn rain under a roof
  (baked into t08/t11 by the image model) cannot be fixed in post.
- **Additive light must respect foreground**: the blue pulse lit the dark silhouette of the officer;
  weight it by the drawing's own brightness.
- **The gate misses what the whole-cut judge catches**: text on a glove box, mangled trolley wheels,
  a melting camera, tape ending in mid-air, floating lanterns, active flames on an extinguished fire.
  Complex mechanical objects (trolleys, cameras, logos on cars) are where the image model fails —
  prefer simple objects. A brand emblem on the hearse was removed by hand (cv2.inpaint).
- **Maps from OpenStreetMap** (`sec2/osm.py`, `sec2/maps.py`): Overpass main server gave 504s and
  resets; the mirror maps.mail.ru worked. Three villages called Ejby in the region — label only what
  the narration names; the find site is not marked ("en skov nær Køge"). Waterlining by distance
  transform; fine hatching aliases when the layer is shown downscaled (use ≥ 11 px spacing or flat
  tone). Region → city zoom = two layers crossfaded at 6–4 km view width, target glides to centre.
- Sound bed changes (rain ↔ muffled rain indoors) need ~2 s ramps; 0.5 s was judged "jarring".
- `sec2/clips.py` take numbering counted the judge's `_use.mp4` cuts (new takes became t5/t6 and the
  judge compared four). Fixed. `pkill -f` killed the calling shell again — kill by PID only.
