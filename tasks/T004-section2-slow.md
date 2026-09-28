# T004 — Section 2 (5:06 → 9:02): slower, subtler, real maps

Status: delivered for Lukas's evaluation 2026-09-28 · waiting on his verdict (QUESTIONS Q7)

## Decision
2026-09-28, Lukas in chat, after watching section 1 (T003):
- The drawn style holds. **Shots may run longer and slower**: fewer, better-chosen shots
  (more thought per prompt), which should also raise quality and lower cost.
- Still too many AI-like movements. Examples: shot 49 (s41, the phone does something
  impossible on itself), shot 32 (s24, plastic "appears from nowhere" instead of being
  pulled off), shot 4 (s04, a half-floating bicycle). **Avoid close-ups of hands doing
  things.**
- **Movement should often be much more subtle**: drawings with camera moves plus very
  subtle motion, cheaper if possible; overall more slow-motion, letting shots breathe.
- **Maps for locations — but they must be accurate.** A map may not be a generated
  image.
- Next: a new section from where section 1 ended, 3–4 minutes forward.

## Plan
- 5:06.3 → 9:01.7 (ends on "…den sektionsstue, de kalder drabsstuen."), ≈ 21 shots,
  average ≈ 11 s (section 1: 4.6 s).
- Motion classes: `still` = keyframe + slow sub-pixel camera move + procedural rain /
  light pulse drawn at 12 fps (free); `ambient` = Veo 3.1 Lite, first = last frame,
  audio off, 6 s played at ≈ 0.5× (on twos) — only smoke, steam, running water;
  `map` = OpenStreetMap vector data rendered in the charcoal look, no image model.
- Gate adds: floating objects / impossible physics, hands performing actions.
- Sound: rain bed built in post (muffled indoors), no Veo audio.

## Done
- 21 shots, 5:06.3 → 9:01.5 + 2.5 s tail, average 11.2 s; cuts in the narration's pauses.
- 19 drawings with a slow camera move and rain / lantern flicker / blue beacon added in post;
  2 maps from OpenStreetMap (København → Køge; zoom into Teilumbygningen, Frederik V's Vej).
- Veo was tried on 3 shots (smoke, raindrops on the blanket, water off the tarp); all three failed
  review and were replaced by stills. Final cut: no generated motion.
- Whole-cut review (Gemini 3.1 Pro) twice: v1 → 9 drawings redrawn or reframed, a brand emblem
  removed by hand, street label moved, blue light kept off the silhouette, maps given more tone;
  v2 → rain kept out from under the tarpaulins, sound-bed changes slowed to 2 s, smoke shot → still.
- Spend ≈ $11.20 list (≈ 90 kr), ≈ 23 kr per minute (section 1: ≈ 87).

## Known weaknesses
- t08/t11: the image model drew rain strokes over the case that stands under the tarp.
- t15: distant lanterns can read as floating; t19: the hearse reads as an ordinary estate car.
- Maps are present-day OpenStreetMap, not 1999. Institute interiors are imagined.
