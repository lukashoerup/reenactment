# T003 — Section 1: the first five minutes, drawn (C)

Status: delivered for Lukas's evaluation 2026-09-27 · waiting on his verdict (QUESTIONS Q6)

## Decision
2026-09-27, Lukas in chat: keep the existing children shots from the cold-open test
(a minor issue for now); make the first ~5 minutes of the episode with the new method,
**one version only: C (drawn + video)**; he evaluates before more is spent.

## Done
- Shot list `sec1/shots.py` → `sec1/shots.json`: 68 shots, 0:00–5:06.3 on the episode
  clock, cut on the narration's word timings. 60 new shots, 7 reused drawn clips
  (children, c1/c3/c5/c6/c7 + s36; s35 reuses c2), 1 black beat (c9).
- Keyframes `sec1/keys.py` on Vertex (gemini-3-pro-image, 2 content-neutral style refs,
  optional place ref) with the gate (gemini-3.1-pro-preview): 35 drawings rejected over
  30 shots; 5 kept despite the gate (keypad digits, two officers instead of one).
- Video `sec1/clips.py`: Veo 3.1 Lite on Vertex, 1 take for pinned static shots
  (first = last frame), 2 otherwise, noun negatives; judge picks on the used window;
  11 shots regenerated once with the judge's fix. 109 takes made, 60 used.
- Cut `sec1/edit.py` → `out/sec1_C_v2.mp4` (5:06, 1280×720, 24 fps, episode audio +
  ducked rain/fire bed, "REKONSTRUKTION · TEGNET MED AI" label for 7 s).
- Review page: `page2/` → artifact "Det Brændende Lig 0:00–5:06" (streamed, clickable
  storyboard, what the machine caught, known weaknesses, cost).
- Spend: **$55.26 list** of the $300 Google Cloud trial credit — video 36.90, images
  12.07, image gate 2.04, video judge 4.25. ≈ $11 per finished minute.

## Known weaknesses (for the next pass, if any)
- Children shots are the old test clips (swirly flames in c5, a child walks out in c6).
- s06 and c2 have no rain: every rain take blinked on and off; the judge failed all,
  the calmest take was chosen by hand. Next time: rain as a post overlay, not from Veo.
- s13 lighter-fluid bottle has a pictogram that can read as a skull.
- s41 slowed to 0.87× to fill its slot; the phone keeps ringing after pick-up.
- s42 has police-radio sound Veo invented. Next time: `generateAudio: false` for all
  takes and build sound in post (the judge does not reliably catch audio).

## Next (only after Lukas's verdict)
- Go: the remaining 39:31. Recipe as here ≈ $11/min (≈ 3,900 kr list for the episode);
  stills-first mix (25 % moving) ≈ 1,500–2,000 kr. Trial credit left ≈ $245 ≈ 20 min.
- Children: QUESTIONS Q5.
