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
# look v3 (finishing pass): postprocessing 6.37 (Zlib, pmndrs), N8AO 1.10 (CC0), three.js Pass.js r170 (MIT),
# Poly Haven textures (CC0)
cd vendor
mkdir -p tex addons/postprocessing
[ -s postprocessing.js ] || curl -sfL -o postprocessing.js "$j/postprocessing@6.37.0/build/index.js"
[ -s n8ao.js ] || curl -sfL -o n8ao.js "$j/n8ao@1.10.1/dist/N8AO.js"
[ -s addons/postprocessing/Pass.js ] || curl -sfL -o addons/postprocessing/Pass.js "$j/three@0.170.0/examples/jsm/postprocessing/Pass.js"
ph() {  # asset resolution map...
  a=$1; r=$2; shift 2
  meta=""
  for m in "$@"; do
    f="tex/${a}_${m}_${r}.jpg"; [ -s "$f" ] && continue
    [ -n "$meta" ] || meta=$(curl -sfL -A "reenactment-gfx" "https://api.polyhaven.com/files/$a")
    url=$(printf '%s' "$meta" | python3 -c "import json,sys; print(json.load(sys.stdin)['$m']['$r']['jpg']['url'])")
    curl -sfL -A "reenactment-gfx" -o "$f" "$url"
  done
}
ph forest_floor 2k Diffuse nor_gl Rough
ph bark_brown_02 1k Diffuse nor_gl
ph brown_mud_02 1k Diffuse nor_gl Rough
ph rock_boulder_dry 1k Diffuse nor_gl
echo ok
