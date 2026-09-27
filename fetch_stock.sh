#!/bin/bash
# Mixkit clips and sound effects used by comp.py, scene.py and assemble.py (Mixkit free licence).
set -e
cd "$(dirname "$0")"
mkdir -p stock/hd sfx elements/fire45676 elements/fire45676_b
for id in 45676 31352 48299; do
  [ -s stock/hd/$id.mp4 ] || curl -sfL --retry 3 -o stock/hd/$id.mp4 "https://assets.mixkit.co/videos/$id/$id-720.mp4"
done
for id in 1262 1330 1329; do
  [ -s sfx/$id.mp3 ] || curl -sfL --retry 3 -o sfx/$id.mp3 "https://assets.mixkit.co/active_storage/sfx/$id/$id-preview.mp3"
done
ffmpeg -v error -y -i stock/hd/45676.mp4 -vf fps=24 -q:v 2 elements/fire45676/f_%04d.png
python3 - <<'PY'
import shutil
n, off = 480, 137
for i in range(1, n + 1):
    j = ((i - 1 + off) % n) + 1
    shutil.copyfile(f"elements/fire45676/f_{j:04d}.png", f"elements/fire45676_b/f_{i:04d}.png")
PY
echo ok
