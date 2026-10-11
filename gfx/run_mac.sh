#!/bin/bash
# Set up and render the four test scenes of "Det Brændende Lig" on a Mac (Apple Silicon).
# 3D shots use the Mac's GPU through ANGLE/Metal (see GL_ARGS in gfx/maptiles.py).
#
#   git clone -b task/T005-look-v3-figures https://github.com/lukashoerup/reenactment.git ~/reenactment-render
#   bash ~/reenactment-render/gfx/run_mac.sh
#
# Safe to re-run: every step skips what is already done, and rendered shots are cached.
# Python + ffmpeg come from conda-forge (Anaconda/Miniconda/Miniforge), else Homebrew,
# else the system python with a bundled ffmpeg. Everything lives in .gfxenv/ (git-ignored).
# Log: out/gfx/mac_run.log.  SCENES="S1-fundet S3-spor" bash gfx/run_mac.sh renders a subset.
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"
mkdir -p out/gfx
exec > >(tee -a out/gfx/mac_run.log) 2>&1
step() { echo; echo "== $(date +%T)  $*"; }
ENV="$REPO_DIR/.gfxenv"

step "Python and ffmpeg"
if [ ! -x "$ENV/bin/python" ]; then
  CONDA=""
  for c in "$(command -v conda 2>/dev/null || true)" "$HOME/anaconda3/bin/conda" "$HOME/miniconda3/bin/conda" \
           "$HOME/miniforge3/bin/conda" "/opt/homebrew/anaconda3/bin/conda" "/opt/anaconda3/bin/conda"; do
    if [ -n "$c" ] && [ -x "$c" ]; then CONDA="$c"; break; fi
  done
  if [ -n "$CONDA" ]; then
    echo "conda: $CONDA"
    "$CONDA" create -y -q -p "$ENV" --override-channels -c conda-forge python=3.11 ffmpeg pip
  elif command -v brew >/dev/null 2>&1; then
    echo "homebrew"
    brew install ffmpeg python@3.11
    "$(brew --prefix)/opt/python@3.11/bin/python3.11" -m venv "$ENV"
  else
    echo "system python + bundled ffmpeg"
    python3 -m venv "$ENV"
    "$ENV/bin/python" -m pip install -q imageio-ffmpeg
    ln -sf "$("$ENV/bin/python" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')" "$ENV/bin/ffmpeg"
  fi
fi
export PATH="$ENV/bin:$PATH"
PY="$ENV/bin/python"
"$PY" --version; ffmpeg -version | head -1

step "Python packages and Chromium"
"$PY" -m pip install -q --upgrade pip
"$PY" -m pip install -q playwright numpy pillow faster-whisper
"$PY" -m playwright install chromium chromium-headless-shell

step "Fonts, libraries, textures"
bash gfx/fetch_assets.sh

step "Episode audio"
[ -s audio/episode.mp3 ] && echo "already here" || "$PY" fetch_audio.py

step "Transcript (word timings)"
if [ -s audio/transcript.json ]; then echo "already here"; else
  "$PY" transcribe.py 02:55-05:32 10:40-13:10 14:25-17:12 36:23-37:53
fi

CORES=$(sysctl -n hw.perflevel0.physicalcpu 2>/dev/null || sysctl -n hw.physicalcpu)
WORKERS=${WORKERS:-$(( CORES > 6 ? 6 : CORES ))}
SCENES=${SCENES:-"S1-fundet S2-obduktionen S3-spor S4-dommen"}
step "Rendering $SCENES at 960x540 on $WORKERS workers"
T0=$(date +%s)
for s in $SCENES; do
  t=$(date +%s); echo "-- $s $(date +%T)"
  "$PY" -m gfx.render "episodes/braendende-lig/scenes/$s.json" --draft --workers "$WORKERS"
  echo "   $s wall $(( $(date +%s) - t )) s"
done
step "ALL DONE in $(( ($(date +%s) - T0) / 60 )) min. Videos: out/gfx/*_540.mp4"
open out/gfx 2>/dev/null || true
