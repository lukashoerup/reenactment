# Cost

Prices: Gemini API list prices, Sept 2026 (Veo 3.1 Fast $0.10/s at 720p, Veo 3.1 Lite
$0.05/s, Nano Banana Pro 2K $0.134/image, Gemini 3.1 Pro $2/M in + $12/M out).
Danish credits move by list × 1.25 VAT → **1 USD ≈ 8 kr** (6.4 kr/USD × 1.25).

## What this test actually cost (2026-09-27)
| Item | USD list | kr incl. VAT |
|---|---|---|
| 21 keyframes (A + drawn redraws) | 2.81 | 22 |
| Veo Fast, 8 clips (36 s) — A1 | 3.60 | 29 |
| Veo Lite, 8 clips (36 s) — C | 1.80 | 14 |
| A2 loop: 2 Lite takes, 1 Fast take, 5 Pro judge calls | ≈1.1 | ≈9 |
| Total (all four versions + A2) | ≈9.3 | ≈75 |
A alone (A1 + A2) ≈ 50 kr for 22.7 s of finished film ≈ 2.2 kr per second — with
first-run waste, one take per shot and a very dense cut (2.8 s per shot).

## Per finished shot, with the v2 flow (2 keyframe candidates, 2 video takes of 6 s,
pairwise judge, 30 % of shots needing another round)
| Shot type | USD | kr |
|---|---|---|
| Photographic, video (Veo Fast) | 1.96 | ≈16 |
| Drawn, video (Veo Lite) | 1.18 | ≈9 |
| Still with camera move (either style) | 0.28 | ≈2 |

## One episode (44:37, average shot 5 s ⇒ ≈ 535 shots)
| Scenario | kr (machine only) |
|---|---|
| Photographic, every shot moving | ≈ 8,400 |
| Photographic, 25 % moving + 75 % stills | ≈ 3,000 |
| **Drawn, every shot moving** | ≈ 5,000 |
| **Drawn, 25 % moving + 75 % stills** | ≈ 2,100 |
Moving shots go where something happens; interview passages carry stills. The August
estimate for a stills-first episode (~2,400 kr) is in the same range.

## Not included
- Human time: Lasse approving the shot list (2–3 h) and the contact sheets (3–4 h);
  an editor's finishing pass (1–2 days). Claude session time (counts against Lukas's
  plan limits, not money).
- Upscaling (e.g. Topaz) or licensed fire/rain plates, if used.

## Quota is the real blocker
A fully moving episode needs ≈ 1,400 video generations. The Gemini API project allowed
10 per day per Veo model ⇒ months. Options: Vertex AI (≈ 50 requests/min per model,
up to 4 videos per request, audio can be switched off — cheaper), Gemini API tier
upgrade (Tier 2 after $100 paid + 3 days) plus the increase form, or a reseller (fal,
Replicate) at similar prices. See RESEARCH §5.
