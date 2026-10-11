#!/bin/bash
# Fonts (SIL OFL) and JS libraries for method E. Not stored in git; fetched once.
#   Archivo (Omnibus-Type) and Newsreader (Production Type), from github.com/google/fonts
#   MapLibre GL JS 5 (BSD-3) — only used to bake map tiles; three.js r170 (MIT) — objects
set -e
cd "$(dirname "$0")/web"
mkdir -p fonts vendor
g=https://raw.githubusercontent.com/google/fonts/main/ofl
for f in "archivo/Archivo%5Bwdth,wght%5D.ttf" "archivo/Archivo-Italic%5Bwdth,wght%5D.ttf" \
         "newsreader/Newsreader%5Bopsz,wght%5D.ttf" "newsreader/Newsreader-Italic%5Bopsz,wght%5D.ttf"; do
  n=$(basename "$f" | sed 's/%5B/[/;s/%5D/]/')
  [ -s "fonts/$n" ] || curl -sfL -o "fonts/$n" "$g/$f"
done
[ -s fonts/OFL-archivo.txt ] || curl -sfL -o fonts/OFL-archivo.txt "$g/archivo/OFL.txt"
[ -s fonts/OFL-newsreader.txt ] || curl -sfL -o fonts/OFL-newsreader.txt "$g/newsreader/OFL.txt"
j=https://cdn.jsdelivr.net/npm
[ -s vendor/maplibre-gl.js ] || curl -sfL -o vendor/maplibre-gl.js "$j/maplibre-gl@5/dist/maplibre-gl.js"
[ -s vendor/three.module.js ] || curl -sfL -o vendor/three.module.js "$j/three@0.170.0/build/three.module.js"
echo ok
