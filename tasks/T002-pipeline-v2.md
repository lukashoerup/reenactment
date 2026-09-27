# T002 — Pipeline v2 (research → code)

Status: open · Blocked on: QUESTIONS.md Q1 (Vertex/GCP) for steps 5–6

## Do
1. `continuity.json` per scene (cast, clothes incl. boots, heights, objects, light,
   weather); `gen_image.py`/`gen_video.py` append it verbatim; judge receives it.
2. Keyframe gate: judge each keyframe (image) before any video spend — faces in
   textures, extra people, continuity vs reference frames.
3. Motion prompts: camera + ambient motion only; noun negatives where supported
   ("thrown object, stick, hand, person entering frame"); static shots with
   first frame = last frame.
4. Judge v2: 12 fps + high media resolution; per-shot brief; pairwise with order swap;
   3 runs merged; checklist grown from docs/REVIEW defects; compare against the best
   existing take, not a fixed score.
5. Vertex AI backend for Veo (4 videos/request, audio off, `enhancePrompt:false`,
   lossless) — needs a GCP project with billing.
6. Bake-off on the five worst shots: Omni 1.1 Flash vs Veo 3.1 Fast vs MiniMax H3 Max
   (check EEA "no minors in uploaded images" for Omni).
7. Post: real fire/rain plates option; per-shot grain seed; J-cuts; spot foley.
8. Cue sheet (prompt, model, date, timecode per shot) + "Rekonstruktion" label.
9. Two- to three-minute segment test from Lasse's timecodes, drawn style, stills-first
   with 25 % moving shots — the realistic episode recipe (docs/COST.md).
