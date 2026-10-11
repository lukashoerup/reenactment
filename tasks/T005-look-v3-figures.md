# T005 — Method E v3: faceless figures, finishing pass, less echo, faster renders

Status: built 2026-10-11 · Branch `task/T005-look-v3-figures` (on top of T003 `dc355f1`)
Review doc: https://claude.ai/code/artifact/a17d49e6-8eef-49a8-a6bb-ee2630c5ebff

## Why
Review of Method E v2: the screen repeats the narration, the 3D reads as a mobile game, renders
take hours on the 2-core cloud machine. Lukas (2026-10-11): people are fine as faceless
figures, like Fern; run it on the MacBook.

## Done
- `diorama`: faceless figures (`figure` item, cast in case.json, poses, walk/run along paths);
  finishing pass on by default (`look:"v3"`): CC0 scanned textures, smooth shading, firelight
  shadows, half-float HDR, N8AO, bloom on the fire, depth of field, vignette. `object` gets the
  same finish. Render version pinned `v3-figures-1`.
- Scenes S1–S4: figures where people act; on-screen text that echoed the narration removed;
  injury details left in the audio.
- `--lint` warns on echo (on-screen text that repeats the narration within ±5 s; names exempt).
- Anchors prefer the match within ±2.5 s and fall back to the written time when a new Whisper
  run hears a phrase differently.
- Type: body 46 px, small 32 px; unspoken quote words at 45 % (was 17 %).
- GL: Mesa llvmpipe on Linux (2.6–3.5× faster than SwiftShader), Metal on macOS; the WebGL
  renderer string is logged. `--draft` renders 960×540. `gfx/run_mac.sh` sets up and renders.

## Open
1. Benchmark on the Mac: confirm the renderer string says Metal, record s/frame per template.
2. Walk cycles: the procedural gait is fine at distance; close-ups want motion capture.
3. Trees still read as game assets (cone and lollipop shapes).
4. Sound design beyond the rain bed.
