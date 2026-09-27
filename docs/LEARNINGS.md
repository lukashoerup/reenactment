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
