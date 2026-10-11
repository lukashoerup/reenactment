"""Local HTTP server for the renderer: static files + caching map-tile proxy.

The browser only ever talks to 127.0.0.1, so renders are reproducible: every tile,
style and photo is fetched once into cache/ and served from disk afterwards
(GFX_OFFLINE=1 refuses to fetch at all).

Routes
  /web/...                 gfx/web (runtime, templates, fonts, vendor libs)
  /ep/...                  the episode folder (case.json assets, photos, geojson)
  /tiles/vec/z/x/y.pbf     OpenFreeMap vector tiles (OpenMapTiles schema, ODbL)
  /tiles/sat/z/x/y.jpg     aerial imagery: Esri World Imagery by default, or SDFI
                           (Danish orthophotos, current or historic) when DF_TOKEN is set
                           and GFX_SAT=sdfi:<layer>
"""
import http.server, json, math, os, socketserver, threading, time, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
CACHE = os.path.join(REPO, "cache")
UA = "reenactment-gfx/0.2 (private research render; contact lukas@hoerup.dk)"
OFFLINE = os.environ.get("GFX_OFFLINE") == "1"
_lock = threading.Lock()
_ofm_url = None


def fetch(url, dest, timeout=30):
    if os.path.exists(dest):
        return dest
    if OFFLINE:
        return None
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            data = urllib.request.urlopen(req, timeout=timeout).read()
            tmp = dest + ".part"
            open(tmp, "wb").write(data)
            os.replace(tmp, dest)
            return dest
        except urllib.error.HTTPError as e:
            if e.code in (204, 404):
                open(dest, "wb").close()  # empty tile: remember the miss
                return dest
            time.sleep(1 + attempt)
        except Exception:
            time.sleep(1 + attempt)
    return None


def ofm_template():
    global _ofm_url
    with _lock:
        if _ofm_url:
            return _ofm_url
        p = os.path.join(CACHE, "ofm_planet.json")
        if not os.path.exists(p) or (not OFFLINE and time.time() - os.path.getmtime(p) > 7 * 86400 and False):
            fetch("https://tiles.openfreemap.org/planet", p)
        _ofm_url = json.load(open(p))["tiles"][0]
        return _ofm_url


def tile_bbox_3857(z, x, y):
    n = 2 ** z
    size = 2 * math.pi * 6378137 / n
    minx = -math.pi * 6378137 + x * size
    maxy = math.pi * 6378137 - y * size
    return minx, maxy - size, minx + size, maxy


def sat_url(z, x, y):
    src = os.environ.get("GFX_SAT", "esri")
    if src.startswith("sdfi:") and os.environ.get("DF_TOKEN"):
        layer = src.split(":", 1)[1]           # e.g. orto_foraar or a historic layer name
        service = os.environ.get("DF_SERVICE", "orto_foraar_DAF")
        b = tile_bbox_3857(z, x, y)
        q = urllib.parse.urlencode({"service": "WMS", "version": "1.1.1", "request": "GetMap", "layers": layer,
                                    "styles": "", "srs": "EPSG:3857", "bbox": ",".join(f"{v:.2f}" for v in b),
                                    "width": 256, "height": 256, "format": "image/jpeg",
                                    "token": os.environ["DF_TOKEN"]})
        return f"https://api.dataforsyningen.dk/{service}?{q}", f"sdfi_{layer}"
    return (f"https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "esri")


class Handler(http.server.SimpleHTTPRequestHandler):
    ep_dir = None

    def log_message(self, *a):
        pass

    def send_file(self, path, ctype):
        if not path or not os.path.exists(path):
            self.send_error(404)
            return
        data = open(path, "rb").read()
        if not data and ctype.startswith("application/x-protobuf"):
            self.send_response(204)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?")[0])
        parts = path.strip("/").split("/")
        try:
            if parts[0] == "tiles" and parts[1] == "vec":
                z, x, y = parts[2], parts[3], parts[4].split(".")[0]
                url = ofm_template().replace("{z}", z).replace("{x}", x).replace("{y}", y)
                dest = os.path.join(CACHE, "tiles", "ofm", z, x, y + ".pbf")
                return self.send_file(fetch(url, dest), "application/x-protobuf")
            if parts[0] == "tiles" and parts[1] == "sat":
                z, x, y = int(parts[2]), int(parts[3]), int(parts[4].split(".")[0])
                url, tag = sat_url(z, x, y)
                dest = os.path.join(CACHE, "tiles", tag, str(z), str(x), f"{y}.jpg")
                return self.send_file(fetch(url, dest), "image/jpeg")
            if parts[0] == "maptile":
                key, z, x, y = parts[1], parts[2], parts[3], parts[4].split(".")[0]
                return self.send_file(os.path.join(CACHE, "maptiles", key, z, x, y + ".png"), "image/png")
            if parts[0] == "web":
                return self.send_file(os.path.join(ROOT, "web", *parts[1:]), self.guess_type(path))
            if parts[0] == "ep" and self.ep_dir:
                return self.send_file(os.path.join(self.ep_dir, *parts[1:]), self.guess_type(path))
        except Exception as e:  # never crash the server mid-render
            self.send_error(500, str(e))
            return
        self.send_error(404)


Handler.extensions_map.update({".js": "application/javascript", ".mjs": "application/javascript",
                               ".ttf": "font/ttf", ".json": "application/json", ".geojson": "application/json"})


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def start(ep_dir, port=0):
    Handler.ep_dir = ep_dir
    srv = Server(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


if __name__ == "__main__":
    import sys
    s, base = start(sys.argv[1] if len(sys.argv) > 1 else None, 8765)
    print("serving", base)
    while True:
        time.sleep(3600)
