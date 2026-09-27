# Research — how to make AI re-enactment look real (Sept 2026)

Three parallel web research passes on 2026-09-27 (AI video practice, film craft,
Blender). Claims carry the source the researcher cited; items marked *unverified* were
not confirmed. Prices and rankings move fast — re-check before spending.

## 1. Models and tools
- Blind-vote rankings (Artificial Analysis): image-to-video #1 MiniMax H3 Max, #3
  **Gemini Omni 1.1 Flash**, #11 Veo 3.1. https://artificialanalysis.ai/video/leaderboard/image-to-video
- **Gemini Omni 1.1 Flash** (27 Aug 2026) runs on the same Gemini key; Google calls it
  the default video model: first+last frame, first frame + reference images in one call,
  chat-style fixes of its own output, extension to 40 s, 360p drafts at ⅓ cost, ~$0.10/s
  at 720p. **EEA limit: no uploaded images containing minors** — a problem for scenes with
  children. https://ai.google.dev/gemini-api/docs/omni · https://ai.google.dev/gemini-api/docs/video
- Seedance 2.0 (up to 9 image refs, 15 s multi-shot), Kling 3.0 (element binding,
  start/end frames), Runway Aleph 2 (edit one frame, change propagates — fix instead of
  regenerate), Luma Ray 3.2 video-to-video. Sora API discontinued 24 Sep 2026 (*per
  OpenAI help page, not re-checked*).

## 2. Techniques against the "AI look" and invented motion
- Image-to-video prompts should describe **motion only**; camera-only motion is most
  reliable; one moment per clip. (Google best practice)
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/best-practice
- Veo's built-in prompt rewriter (`enhancePrompt`, on by default) is blamed for invented
  objects; try `false` on Vertex (*unverified that Veo 3.1 honours it*).
- `negativePrompt` works with nouns ("thrown object, stick, hand, person"), not "no X".
- Static shots: "Static shot, the camera remains completely still… single continuous
  shot, no cuts… the subject remains still, only the flames change".
- **Pin both ends:** same keyframe as first and last frame ⇒ the clip must return to the
  start state — strongest guard against events (*inference, untested*).
- Same character/object description word for word in every prompt; reuse seeds; Veo
  "ingredients" (≤ 3 reference images, 8 s clips only).
- Generate 4–8 short takes, cut the best 2–4 s.
- Replace generated flames with **real fire plates**; upscale with Topaz Starlight
  (keeps grain/motion blur); grade: LUT 50–70 %, grain 8–15 %, sub-pixel softening,
  halation, gate weave. https://www.actionvfx.com/blog/creating-realistic-fire-using-vfx-stock-footage
- Stylisation is "more forgiving of AI anomalies" than photorealism — Al Jazeera's *True
  Crime Reports* uses stylised stills (8M+ views).
  https://dantaylorwatt.substack.com/p/visualising-podcasts-using-ai

## 3. Film craft to copy (re-enactment directors)
- **"Feet to the door, not the knock."** Unsolved Mysteries (Netflix) director Marcus A.
  Clarke: show partial action, no "see-say" of the narration.
  https://www.pressreader.com/canada/toronto-star/20201012/282123523979445
- Errol Morris (*The Thin Blue Line*): stylised, object close-ups, slow motion only at
  chosen moments; re-enactments deepen the mystery. The Keepers: black-and-white.
  https://www.criterion.com/current/posts/3500-the-thin-blue-line-a-radical-classic
- Never mix period styles within a scene (Oxygen *Snapped* team).
- Script supervisor = continuity bible: wardrobe, props, heights, screen direction,
  eyelines, lens per shot. Coverage: wide → medium → close → inserts.
- Motivated camera movement only (follow action, reveal, POV). 35–50 mm "honest";
  telephoto for tension. "Motion that doesn't carry weight reads as animated."
- Editing: cut on action; Dmytryk — never cut without a reason, cut in movement;
  Murch — emotion first; avg 4–6 s per shot; J-cuts (sound before picture); build
  sequences, not wallpaper B-roll.
- Sound: never digital silence; ambience beds + spot foley per visible action; dialogue
  anchors loudness (EBU R128 −23 LUFS; YouTube ≈ −14).
- Look: one motivated light source per scene (firelight), 180° shutter motion blur,
  handheld micro-movement ("too smooth is a giveaway"), grain that differs slightly per
  shot. https://higgsfield.ai/blog/ai-video-look-real-2026 ·
  https://noamkroll.com/why-most-film-grain-looks-fake-and-how-to-achieve-better-results-in-post-production/
- Dailies: review every take for focus, exposure, continuity, coverage — i.e. our judge.

## 4. Automated review — what the literature says
- Artifact-Bench (19 models): Gemini 3.1 Pro best, still only 74 % on real-vs-AI and
  < 10 % at pinpointing specific artifacts; humans 87.7 %. https://arxiv.org/html/2605.18984v1
- Gemini samples video at **1 fps by default** — set `fps` and `media_resolution`.
- **Pairwise comparison with a rubric, run twice with order swapped**, matched human
  rankings far better than absolute scores (0.872 vs 0.672). https://arxiv.org/html/2608.09111v1
- Checklist tuned per judge from ~200 human ratings: +32 % agreement. https://arxiv.org/html/2606.22918
- ⇒ Our experience matches: judge found the big story errors, missed small continuity,
  varied between runs.

## 5. Cost and quota
- Gemini API: Veo 3.1 $0.40/s; Fast $0.10 (720p)/$0.12 (1080p); Lite $0.05/$0.08;
  Omni ≈ $0.10/s (720p). https://ai.google.dev/gemini-api/docs/pricing
- **Vertex AI**: stable `veo-3.1-generate-001` / `veo-3.1-fast-generate-001`
  (us-central1), audio can be switched off (cheaper), ≈ 50 requests/min per model, up to
  4 videos per request, `enhancePrompt`, `compressionQuality`.
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/veo/3-1-generate
- Gemini API limits are per project; Veo daily numbers only visible in AI Studio; Tier 2
  after $100 paid + 3 days; increase form: https://forms.gle/ETzX94k8jf7iSotH9
- Resellers: fal (Veo Fast $0.10/s no audio), Replicate similar; MiniMax H3 Max on fal.

## 6. Blender — when it works
- Realistic Blender work = scanned assets (Poly Haven, BlenderKit, Megascans ~$0.99/asset
  since 2025, Botaniq, Geo-Scatter), mocap for people (Mixamo, Rokoko, GVHMR from phone
  video), real camera shake (Camera Shakify), AgX/Filmic colour, GPU rendering. A forest
  film recreation took ~3.5 months part-time on an RTX laptop.
  https://80.lv/articles/recreating-a-scene-from-the-rorschach-film-using-blender-megascans
- Ian Hubert: projects real footage onto simple geometry; hand-animating 2 s of a person
  "a week… still wouldn't have looked as good".
- Where it shines for true crime: **forensic reconstructions** (Forensic Architecture:
  photos projected on minimal models), **maps and routes** (BlenderGIS, Blosm), stylised
  NPR/Grease Pencil looks, previz.
- **Hybrid:** Blender greybox + depth/normal/pose/mask passes → AI renders the look
  (Mickmumpitz "AI Renderer 2.0" with Wan 2.1 VACE; Luma Ray 3.2 / Runway Aleph
  video-to-video). Needs a GPU (≥ 16 GB VRAM or rented 4090 at ~$0.35–0.75/h). Veo takes
  no video input — Blender can only guide it through first/last keyframes.
- Blender MCP (Claude driving Blender): fine for assembling scenes, fails at foliage,
  organic shapes and animation.
- Our D looked like a game because: cylinder trees, doll figures without cloth/hair/mocap,
  fire that lights nothing, dry-looking surfaces, 10 samples, no motion blur/DOF/real
  shake. Realistic 25 s forest scene ≈ 40–80 h for an experienced artist (*estimate*).

## 7. Ethics and labelling
- Archival Producers Alliance (2024): watermark AI material during editing; tell viewers
  (lower third / narration / opening card); keep a cue sheet of prompts, tools, dates,
  timecodes. https://www.pbs.org/standards/blogs/standards-articles/archival-producers-alliance-develops-guidelines-for-ai-use-in-documentaries/
- YouTube requires disclosure of realistic scenes that did not occur. EU AI Act art. 50
  labelling (from Aug 2026, possibly delayed to Dec 2026).
- Backlash cases: *What Jennifer Did* (AI-altered photos presented as real), *Gabby
  Petito* (AI voice), *Lucy Letby* (AI-anonymised faces, "robotic dead look").

## What we change (merged, ranked)
1. **Continuity bible** (JSON) per scene: cast, clothes incl. boots, relative heights,
   objects (the bundle), light source, weather — injected verbatim in every prompt and
   given to the judge with reference frames.
2. **Motion discipline:** camera + ambient motion only; nouns in `negativePrompt`;
   first frame = last frame for static shots; `enhancePrompt:false` (Vertex).
3. **Keyframe review before video** — cheapest place to catch faces in textures, extra
   people, wrong boots.
4. **More, shorter takes** (4 × 4–6 s) and pairwise judging (order-swapped), 8–12 fps.
5. **Move to Vertex AI** (quota, 4 videos/request, audio off) and run a bake-off:
   Omni 1.1 Flash vs Veo 3.1 vs MiniMax H3 on the worst shots (check the EEA minors rule).
6. **Drawn style as default** (Lukas's pick; also the most forgiving).
7. **Real fire/rain plates** composited over generated shots; per-shot grain variation.
8. **Edit like an editor:** 4–6 s average, cut on action, J-cuts, sound bed + spot foley.
9. **Label + cue sheet:** "Rekonstruktion" on screen; log every generated shot.
10. **Blender only for** maps/routes, crime-scene layouts and previz — or as control
    passes when a GPU and a video-to-video model are available.
