"""Bake the film's map style into 512-px raster tiles, once, and reuse them everywhere.

Shots composite these tiles (gfx/web/templates/map.js), so a map frame renders as fast as
a text frame, and a place shown in five scenes is drawn once. The cache key is a hash of
gfx/web/mapstyle.js: change the style and every tile is re-baked.
"""
import sys, base64, hashlib, io, os, time

from PIL import Image

GFX = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(GFX), "cache", "maptiles")
# WebGL backend. Mesa llvmpipe (gl-egl) is 2.6-3.5x faster than SwiftShader on CPU-only Linux
# (measured 2026-10-11); macOS with a GPU: GFX_GL=metal. GFX_GL=swiftshader restores the old path.
_GL = {
    "llvmpipe": ["--use-gl=angle", "--use-angle=gl-egl", "--ignore-gpu-blocklist"],
    "metal": ["--use-gl=angle", "--use-angle=metal", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"],
    "swiftshader": ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
}
GL_ARGS = _GL[os.environ.get("GFX_GL", "metal" if sys.platform == "darwin" else "llvmpipe")] + ["--font-render-hinting=none"]
BLOCK = 2  # tiles per side per render (1024 px): bigger blocks are much slower in SwiftShader


def tile_key():
    return hashlib.sha1(open(os.path.join(GFX, "web", "mapstyle.js"), "rb").read()).hexdigest()[:8]


def tile_path(key, z, x, y):
    return os.path.join(CACHE, key, str(z), str(x), f"{y}.png")


def bake(tiles, base, key):
    """tiles: iterable of 'z/x/y'. Renders the missing ones in 4×4 blocks."""
    need = set()
    for t in tiles:
        z, x, y = map(int, t.split("/"))
        if not os.path.exists(tile_path(key, z, x, y)):
            need.add((z, x, y))
    if not need:
        return 0
    blocks = sorted({(z, (x // BLOCK) * BLOCK, (y // BLOCK) * BLOCK) for z, x, y in need})
    from playwright.sync_api import sync_playwright
    t0 = time.time()
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=GL_ARGS)
        pg = br.new_page(viewport={"width": 2048, "height": 2048}, device_scale_factor=1)
        pg.on("pageerror", lambda e: print("  [tilegen error]", e, flush=True))
        pg.goto(base + "/web/tilegen.html")
        pg.wait_for_function("typeof renderBlock === 'function'")
        for z, bx, by in blocks:
            n = min(BLOCK, 2 ** z)
            url = pg.evaluate("a => renderBlock(...a)", [base, z, bx, by, n])
            im = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).convert("RGB")
            for i in range(n):
                for j in range(n):
                    x, y = (bx + i) % (2 ** z), by + j
                    if y >= 2 ** z:
                        continue
                    out = tile_path(key, z, x, y)
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    im.crop((i * 512, j * 512, i * 512 + 512, j * 512 + 512)).save(out + ".part.png", optimize=False)
                    os.replace(out + ".part.png", out)
        br.close()
    print(f"  baked {len(blocks)} map block(s) ({len(need)} tiles needed) in {time.time() - t0:.0f}s", flush=True)
    return len(blocks)
