"""Author-time geography: fill case.json with coordinates and road routes, once.

    python3 -m gfx.geo episodes/<ep>/case.json

places: {"id": {"name": ..., "q": "search text"}}         → adds lat/lon (Nominatim, OSM)
routes: {"id": {"from": "placeId", "to": "placeId"}}       → adds coords (OSRM, OSM roads)
Results are written back into case.json, so renders never depend on these services.
Every coordinate a viewer sees comes from here or is typed in by hand with a note.
"""
import json, sys, time, urllib.parse, urllib.request

UA = "reenactment-gfx/0.2 (private research render; contact lukas@hoerup.dk)"


def get(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read())


def simplify(pts, tol=0.00015):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = (dx * dx + dy * dy) ** 0.5 or 1e-12
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + b[0] * a[1] - b[1] * a[0]) / L
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)
    return [a, b]


def main(path):
    case = json.load(open(path))
    for pid, p in case.get("places", {}).items():
        if "lat" in p or "q" not in p:
            continue
        r = get("https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=dk&q=" + urllib.parse.quote(p["q"]))
        if not r:
            print("not found:", pid, p["q"])
            continue
        p["lat"], p["lon"] = round(float(r[0]["lat"]), 6), round(float(r[0]["lon"]), 6)
        p["source"] = "OSM Nominatim: " + r[0]["display_name"][:120]
        print("place", pid, p["lat"], p["lon"])
        time.sleep(1.1)  # Nominatim policy: max 1 request per second
    for rid, r in case.get("routes", {}).items():
        if "coords" in r:
            continue
        a, b = case["places"][r["from"]], case["places"][r["to"]]
        url = (f"https://router.project-osrm.org/route/v1/driving/{a['lon']},{a['lat']};{b['lon']},{b['lat']}"
               "?overview=full&geometries=geojson")
        d = get(url)["routes"][0]
        r["coords"] = [[round(x, 5), round(y, 5)] for x, y in simplify(d["geometry"]["coordinates"])]
        r["km"], r["min"] = round(d["distance"] / 1000, 1), round(d["duration"] / 60)
        r["source"] = "OSRM on OpenStreetMap roads (today's roads; 1999 may differ)"
        print("route", rid, len(r["coords"]), "pts", r["km"], "km")
    json.dump(case, open(path, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
