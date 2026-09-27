# reenactment

AI-generated re-enactment video for true-crime podcasts, cut to the episode's own
narration. First client test: *Danske Drabssager* S6E5 "Det Brændende Lig" for Bull
House Media. Owner: Lukas. Private repo (real case, client pitch).

## Contract (non-negotiable)
- Work on a branch `task/<task-file-name>`; never directly on `main`.
- **Never commit media or the podcast audio.** `.gitignore` covers `audio/`, `clips/`,
  `kf*/`, `out/`, `render/`, `post/`, `stock/`, `sfx/`, `elements/`, `page/*.mp4`.
  Recreate audio with `python3 fetch_audio.py`.
- **Secrets:** the Gemini key is read from the file named in `$GKEY_FILE`, never from
  code, never logged, never committed. `grep -rlE 'AIza[0-9A-Za-z_-]{30}' .` must be empty before a commit.
- Every paid call appends to `spend.log`. Scripts stop at a spend cap; never raise a
  cap without Lukas. Danish credit = list price + 25 % VAT (≈ 8 kr per USD).
- Series rules (docs/PROJECT.md §Rules) are hard: no faces, no body, nothing that can
  pass for archive, no motion without a visible cause.
- Decisions from chat go into docs/PROJECT.md §Decisions or a task file.

## Document routing (read only what you need)
| Working on...                          | Read first                  |
|----------------------------------------|-----------------------------|
| Goal, client, rules, decisions, status | docs/PROJECT.md             |
| How the pipeline runs, step by step    | docs/METHOD.md              |
| What went wrong and why (dated)        | docs/LEARNINGS.md           |
| What others do (Sept 2026 research)    | docs/RESEARCH-2026-09.md    |
| Cost of a scene / an episode, quotas   | docs/COST.md                |
| Review of A1 → A2 (defect list)        | docs/REVIEW-2026-09-27.md   |
| Open work                              | tasks/, QUESTIONS.md        |
| Cross-project patterns                 | workbench: context/         |

## Files
| File | Does |
|---|---|
| `fetch_audio.py`, `transcribe.py` | episode MP3 from the public RSS feed; faster-whisper (medium, da) with word timings |
| `shotlist.json` | the scene: narration timing, style bible, 8 shots with image + motion prompts |
| `gen_image.py` | keyframe via Gemini image model (`gemini-3-pro-image`), optional `--ref` images |
| `gen_video.py` | image-to-video via Veo 3.1 (Fast/Lite) on the Gemini API |
| `methodB.py` | fallback: still + camera move + fire flicker + rain (no video model) |
| `edit.py` | v1 cut (A1/B/C): trims, grade (halation, film curve, grain), narration + ducked ambience |
| `edit2.py` | v2 cut (A2): frame-accurate, hood blur mask, S7 lift, S8 push-in, rain bed |
| `qa/metrics.py` | free checks: in-shot jumps, luma/colour per shot, sound at cuts (Haar faces: useless) |
| `qa/judge.py` | blind whole-cut review by a Gemini model watching the video with sound |
| `qa/loop.py` | per-shot loop: generate → judge the used window → retry with fix → fallback B |
| `scene.py`, `kid_meta.py`, `comp.py`, `post.py`, `postwatch.py`, `assemble.py`, `render_all.sh`, `fetch_stock.sh` | method D: Blender 3D + stock fire (bpy 4.5, CPU) |
| `gen/generate.py` | untested fal.ai variant of the pipeline (Kling / nano-banana), kept for reference |
| `page/` | source of the review page (Artifact "Børnene og bålet") |

## Commands (from repo root, Python 3.11, ffmpeg)
```
export GKEY_FILE=/path/outside/repo/gkey
python3 gen_image.py kf/S1.png "<prompt>" --ref kf/master.png
python3 gen_video.py clips/S1_v1.mp4 kf/S1.png "<motion prompt>" --dur 6 --model veo-3.1-fast-generate-preview
python3 qa/loop.py S2 S4 S8            # CAP_USD env caps spend
python3 edit2.py out/reenact_A2.mp4
python3 qa/judge.py out/A2_720.mp4 gemini-3.1-pro-preview qa/judge.json 6
bvenv/bin/python qa/metrics.py out/reenact_A2.mp4
```
