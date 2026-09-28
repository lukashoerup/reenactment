# T004 — Section 2 (5:06 → 9:02): slower, subtler, real maps

Status: in progress (2026-09-28)

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
