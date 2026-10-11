# T003 — Method E: graphics instead of generated pictures

Status: first test done 2026-10-11 · Branch `task/T003-graphics-method` · Review page: https://claude.ai/artifact/R3ctHUypFYzMS7zeUR1bJH

## Why
Lukas (2026-10-11): generated images will almost always read as AI. Carry the story with
maps, motion, models and real material instead; readable text is fine. The method must be
robust and flexible enough for a full 45-minute episode.

## Done
- `gfx/`: data-driven renderer. Scene JSON on the episode clock (word anchors) →
  templates (map, siteplan, facts, quote, title, card, timeline, photo, object) →
  deterministic frames in headless Chromium → cut with the episode's own narration.
  Shot cache by content, map tiles baked once, lint, contact sheet, cue sheet.
  Authoring contract: `gfx/CATALOG.md`. How it runs: docs/METHOD.md §Method E.
- `episodes/braendende-lig/case.json`: people, places (OSM), road routes, site layout,
  every on-screen fact with the timecode where it is said.
- Four scenes from Lasse's timecodes (≈ 9 min), no generated images:
  S1 Fundet (02:59–05:27), S2 Obduktionen (10:44–13:05),
  S3 Flasken og dæksporene (14:29–17:08), S4 Dommen (36:27–37:49).
- `transcribe.py` takes windows or `--all`; works with current PyAV (decodes via ffmpeg).

## Open
1. **Names to check with Lasse** before anything is shown outside: the speaker in S4 after
   the host's question (not named on screen now); the crime-scene technician's surname
   (Whisper: "Hyttholm"? — not used on screen); confirm "Hans Petter Hougen" and
   "Bent Isager-Nielsen" as the series spells them.
2. **1999 aerial photos**: SDFI's historic orthophotos are free but need a (free) token from
   dataforsyningen.dk. With `DF_TOKEN` + `GFX_SAT=sdfi:<layer>` the map template uses them;
   the layer name for 1999 still has to be looked up in the service's capabilities.
   Esri imagery (used for tests) is not cleared for broadcast.
3. **Real photographs**: the `photo` template is built but unused — no licensed photos yet
   (Ritzau Scanpix for 1999 press photos, Wikimedia Commons for places; credit on screen).
4. **Mix with re-enactment**: the drawn re-enactment (method C) can sit in this cut as a
   `clip` shot for the two or three peaks (the children at the fire). Template not built.
5. **Full episode**: `transcribe.py --all`, then ~12–15 scene files. Claude can draft each
   from the transcript + CATALOG; a person checks names, facts and taste.
6. Lower thirds for every speaker on first appearance (needs names confirmed, see 1).
7. Licences for production: OSM/OpenMapTiles attribution is on screen; Nominatim and the
   OSRM demo server are fine for author-time use only (low volume).

## Done when
Lasse has seen the four scenes and says which direction to take for a full episode.
