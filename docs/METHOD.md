# Method (as run on 2026-09-27)

Cloud container, 2 CPU, no GPU, ffmpeg, Python 3.11. Paid models via one Gemini API key.

## 1. Audio and timing
1. `fetch_audio.py` pulls the episode MP3 from the RSS feed (the feed can insert ads —
   re-check the timing of the first line before trusting `shotlist.json`).
2. `transcribe.py`: faster-whisper `medium`, `language="da"`, `word_timestamps=True`.
   ~5 min CPU for 5 min audio. Pick the scene from the transcript; the cold open was
   written as pure re-enactment ("Bålets flammer lokker…").
3. Cut points go *before* a line starts (e.g. S2 at 5.21 s, "Selvom" at 5.32 s).

## 2. Shot list = the director's document
`shotlist.json`: per shot `start/end` on the scene clock, the narration line, framing
(lens), action, camera, `prompt_image`, `prompt_motion`, plus a `style_bible`
(place/time, look, camera, cast, never-list). One idea per shot.

## 3. Keyframes (image-first)
- Model `gemini-3-pro-image` (Nano Banana Pro), 2K, 16:9, via `gen_image.py`.
- Master look frame first; every later shot gets `--ref` of an earlier approved frame
  so cast, clothes and light carry over.
- Safety filter: the first master (story words: "true-crime", "bundle", "children") came
  back `OTHER`, a later one `IMAGE_SAFETY`. Plain visual description ("Film still…",
  "old woollen blankets") passed. Children from behind passed.
- Style string appended to every prompt: 35 mm Kodak Vision3 500T, underexposed, grain,
  halation, "not glossy, no teal-and-orange, no lens flare, no text".

## 4. Image-to-video
- `gen_video.py`, Veo 3.1 **Fast** (A1) / **Lite** (C, A2 S2) at 720p, 4–6 s,
  `personGeneration: allow_adult`, `negativePrompt` (Fast only — Lite rejects it).
- Motion prompt describes camera and small motion only, and ends with "Audio: … No music,
  no voices." Generated audio was clean (no speech found by whisper).
- ~33–45 s per clip. Lite gave the drawn look fine; for photoreal it was used once (S2) and passed.

## 5. Method B (no video model)
`methodB.py`: the keyframe with an eased push/drift, sub-pixel handheld noise, flicker on
warm pixels, a synthetic rain layer; ambience muxed from the Veo clip. Cannot invent
motion; also cannot perform.

## 6. Method C (drawn)
Each A keyframe redrawn with the same image model ("charcoal and black ink wash on warm
grey paper… fire in orange pastel… courtroom sketch artist"), then Veo **Lite** with
"every frame keeps exactly the same drawn style… must never turn photographic".
Redraws twice invented extra people (S2, S3) — re-prompted with "no other people".

## 7. Method D (Blender)
`scene.py` builds forest, children (`kid_meta.py`), fire rig; Cycles 10 samples at 70 %
on CPU (~1.5 h for 4 shots); `comp.py` composites stock fire; `post.py` mist, rain,
bloom, grain; `assemble.py` cuts. Looked like a game — see LEARNINGS and RESEARCH.

## 8. Edit and grade
- `edit2.py` (use this, not `edit.py`): cut on **frame numbers**, `trim=start_frame`,
  so picture never drifts from narration.
- Grade in RGB (`format=gbrp` before blends — YUV blending turned everything purple):
  quarter-res highlight bloom tinted red (halation) screened at 0.32, film curve with
  lifted blacks, cool shadows/warm highlights, saturation 0.86, 0.55 px blur, grain 7,
  vignette.
- Sound: narration from the episode (untouched), Veo ambience per shot with 30 ms fades,
  a **continuous rain bed** under everything (no drop-outs at cuts), sidechain ducking
  under the voice, limiter. Integrated ≈ −17 LUFS.
- Local fixes: feathered-ellipse blur mask on S3 hoods (`qa/hoodmask.png`), S7
  brightness/gamma lift, S8 digital push-in via `zoompan` at 2× size.

## 9. Review
- `qa/metrics.py` (free): frame-difference spikes inside shots, mean luma and R−B per
  shot, sound level either side of each cut. Found the 3-frame drift, the dark S7, the
  audio holes. Haar face detection fires on flames — useless.
- `qa/judge.py`: Gemini 3.1 Pro watches the 720p cut **at 6 fps** with sound, gets the
  story, narration timing, shot intents and rules, returns JSON defects with fixes.
- `qa/loop.py`: per shot → generate → judge only the window that will be used (12 fps)
  → pass: keep; fail: retry once with the judge's `fix` appended → fail: method B.
  Per-shot brief; reference image only for shots that contain the object.

## 10. Section scale (sec1, first five minutes, drawn)
1. `sec1/shots.py`: one row per shot on the **episode clock** (start/end from the
   word timings), narration line, image prompt, motion prompt, `pin` (static:
   first = last frame), `ref` (match another keyframe's place/objects), `reuse`
   (existing clip + in-point). A new shot about every 2–8 s, on the words.
2. `sec1/keys.py`: keyframes in waves (a shot waits for its `ref`), 2 style refs,
   gate → one redraw with the gate's "avoid" text → keep with a flag.
3. `sec1/clips.py gen`: Veo 3.1 Lite, 4–8 s, negatives, pinned where possible.
   `pick`: the judge sees exactly the window the edit will use and either picks a take or
   fails it with a one-sentence fix → one more round of 2 takes → picks the best.
4. `sec1/edit.py`: every shot normalised to its exact frame count (slowed only if the
   clip is short, never sped up), concat, light grain + vignette, label, episode audio,
   the takes' own ambience ducked under the narration. Cached per shot, so a single
   replaced shot re-renders in seconds.
5. `page2/build.py`: review page with a storyboard that seeks the video, tags per shot
   (redrawn / re-animated / from the test / weakness).
