# T001 — Fix the remaining defects in the cold open (drawn style first)

Status: open · Needs: Gemini credit (≈ 20–30 kr) and a day with Veo quota left

## Why
A2 is close; Lukas still sees AI tells. Lukas prefers the drawn style (C), so fix the
scene there first, then carry the fixes to A.

## Do
1. **S6 "Et dyr?"** — new keyframe with correct continuity (older child navy/dark boots,
   smaller child red boots and clearly shorter, per S1) and a static motion prompt:
   rain on the puddle, sparks rising, *nothing enters the frame, no logs move*. Use first
   frame = last frame. Free stopgap: crop to the left child's boots (drops the log).
2. **S3** — new take where the lump in the fire reads as blankets, not a head (reference
   = S4 keyframe crop).
3. **S5** — take where the children's hands stay distinct where they touch.
4. **C (drawn)** — remove swirls in S5, keep both children in S6, no figures behind the
   fire in S8; judge every redrawn keyframe for extra people before animating.
5. Run `qa/loop.py` with per-shot briefs; then `qa/judge.py` 3× on the cut and merge.

## Done when
Blind judge (3 runs) reports no blocker/major; Lukas signs off on a TV.
