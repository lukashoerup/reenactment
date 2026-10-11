# reenactment

AI re-enactment video for true-crime podcasts, cut to the episode's own narration.
First test: the cold open of *Danske Drabssager* "Det Brændende Lig", made four ways
(photographic, stills, drawn, Blender), reviewed by eye, by code and by an AI judge,
then fixed by an automatic generate → judge → retry loop.

- Review page: https://claude.ai/artifact/3iJtsqAvHhtWE42YQdAmuu
- Start here: `CLAUDE.md` → `docs/PROJECT.md`
- What we learned: `docs/LEARNINGS.md` · what others do: `docs/RESEARCH-2026-09.md`
- What an episode costs: `docs/COST.md`

**Method E (2026-10-11):** the same story told with maps, site sketches, findings, the
speakers' own words and modelled objects — no generated images. Code in `gfx/`, scenes in
`episodes/braendende-lig/`, see `gfx/CATALOG.md` and `tasks/T003-graphics-method.md`.

Media and podcast audio are not stored here (see `.gitignore`).
