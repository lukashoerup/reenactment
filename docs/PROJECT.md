# Project

## Goal
Picture for true-crime podcast episodes so they can run as video: re-enactments cut to
the episode's own narration, good enough that a viewer watches and nothing reads as
"AI". Commercial angle: a repeatable pipeline where the director (Lasse) gives
film-language notes and the machine does the rest.

## Client and context
- **Bull House Media**, Lasse Eskildsen (founder/CEO; Lukas's uncle). Podcast
  *Danske Drabssager* (Bauer Media / True Crime Agency, host Stine Bolther).
- Test episode: S6E5 **"Det Brændende Lig"** (44:37). Public feed:
  `https://rss.podplaystudio.com/1103.xml`.
- Lasse's timecodes (mail 2026-08-19): 03:30–06:00 children/bonfire/emergency services;
  09:34–13:00 forensic pathologist; 15:30–17:09 lighter fluid, tyre tracks;
  20:17–21:05 sweat, killers, flammable liquid; 36:40–39:36 prosecutor.

## History
| Date | What | Link |
|---|---|---|
| 2026-08-20 | Visual test "Våd aske": 24 mood stills + 4 clips for Lasse's 5 timecodes, **no people**. Lukas: missed the brief — it should have been re-enactment. | https://claude.ai/code/artifact/680baded-fbae-4dc3-940c-6cf7c3eca4af · list: https://claude.ai/code/artifact/964a1bfc-7103-4ac4-9e06-8534e2b6e769 |
| 2026-09-27 | Re-enactment test of the cold open 01:36.6–01:59.3 in four methods (A photo, B stills, C drawn, D Blender), then A2 via the automatic fix loop. | "Børnene og bålet": https://claude.ai/artifact/3iJtsqAvHhtWE42YQdAmuu |
| 2026-10-11 | Method E: four scenes (≈ 9 min) from Lasse's timecodes as maps, site sketches, findings, quotes, modelled objects — no generated images. | "Kort, spor og ord": https://claude.ai/artifact/R3ctHUypFYzMS7zeUR1bJH |

## The scene (cold open, 22.7 s)
> Bålets flammer lokker de nysgerrige børn tættere på. Selvom regnen står ned i stænger,
> buldrer ilden lystigt. Midt i bålet ligger en bylt. På cirka 70 centimeter. Hvad er det?
> Et dyr? Affald? Eller et menneske?

8 shots + black, timed to the words (`shotlist.json`).

## Rules (hard)
1. No recognisable face — backs, hands, feet, silhouettes, objects, places.
2. Never the victim, a body, limbs, blood or injury. The bundle is fabric, always.
3. Nothing that can pass for archive (no fake police photos, news footage, text).
4. ~~No readable text in frame.~~ Readable text is allowed (2026-10-11): designed
   graphics — names, places, times, findings, the speaker's words — never text that
   imitates a document, paper or record (that is rule 3). Period-correct (Denmark, 1999).
5. No AI voices of real people — narration is always the episode's own audio.
6. **Nothing moves without a visible cause** (added 2026-09-27 after thrown logs/sticks).
7. Mark as reconstruction on screen (see RESEARCH: APA guidelines, EU AI Act art. 50).

## Decisions
- 2026-08-20 — No faces / no body / no archive look (rules 1–4), from Lasse's own remark
  that people need not resemble the real ones.
- 2026-09-27 — Narration stays the original podcast audio; ambience (rain, fire) under it.
- 2026-09-27 — Lukas prefers the **drawn style** (page version "C · Tegnet"; he called it
  "B"). Default style for the next round unless Lasse says otherwise.
- 2026-09-27 — Code and learnings live in this private repo; generic lessons also in
  workbench `context/LEARNINGS.md`.
- 2026-10-11 — Lukas: lean less on generated pictures; carry the story with maps, motion,
  models and real material, because generated images will almost always read as AI.
  Method E (graphics rendered from code) built for this; must scale to a full 45-min episode.
- 2026-10-11 — Lukas: readable text in frame is allowed (rule 4 changed).
- 2026-10-11 — Lukas, on the first E cut: maps work well; too many parts are bullet points
  slowly appearing; more on the visuals, in the direction of the YouTube channel Fern; zoom
  into the campfire and show it in 3D. → `diorama` template (3D model of the site) replaces
  the findings lists; the site is a grey rainy day ("en regnvejrsdag", 03:06), not night.

## Status (2026-09-27)
- A2 is the best photographic cut. Known defects left: S6 log swings in as if thrown
  (my prompt asked for "a branch collapses"), S6 boots green + children equal height
  (S1: red boots, smaller child), S3 bundle can read as a head from behind, S5 hands
  blend where they touch. See docs/REVIEW-2026-09-27.md.
- Gemini credits used up (~79 kr); Veo Lite hit a daily cap of 10 videos.
- Next: tasks/T001 (fix the scene, drawn style first), tasks/T002 (pipeline v2).

## Status (2026-10-11)
- Method E rendered four scenes (≈ 9 min, 720p preview) with no generated images; review
  page "Kort, spor og ord". Open: names to confirm with Lasse, SDFI token for 1999 aerials,
  licensed photos, whether the drawn re-enactment goes in for the peaks. See tasks/T003.
