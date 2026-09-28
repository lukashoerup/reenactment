"""Fetch the real map data for section 2's maps from OpenStreetMap (Overpass API) and cache it in sec2/mapdata/.
Data © OpenStreetMap contributors, ODbL 1.0 — the maps credit it on screen. Nothing here is generated.
python3 sec2/osm.py
"""
import json, os, time
import requests

UA = "reenactment-map/0.1 (private documentary test)"
API = os.environ.get("OVERPASS", "https://overpass-api.de/api/interpreter")   # mirror that worked: maps.mail.ru/osm/tools/overpass/api/interpreter
OUT = "sec2/mapdata"; os.makedirs(OUT, exist_ok=True)

# The places the narration names. Teilumbygningen / Retsmedicinsk Institut checked in OSM on 2026-09-28:
# node 12748256266 "Retsmedicinsk Institut" at 55.69833, 12.56646; building ways 25657593 + 89479450 "Teilumbygningen".
REGION = (55.36, 11.80, 55.78, 12.75)           # S, W, N, E — København to Køge and Ejby
C_LAT, C_LON = 55.6980, 12.5665                 # Teilumbygningen
CITY = (C_LAT - 0.0160, C_LON - 0.0500, C_LAT + 0.0160, C_LON + 0.0500)     # ≈ 6.3 × 3.6 km
INNER = (C_LAT - 0.0080, C_LON - 0.0240, C_LAT + 0.0080, C_LON + 0.0240)    # buildings only here

def bb(b): return f"({b[0]},{b[1]},{b[2]},{b[3]})"

QUERIES = {
    "region_coast": f'way["natural"="coastline"]{bb(REGION)};',
    "region_water": f'(way["natural"="water"]{bb(REGION)};relation["natural"="water"]{bb(REGION)};);',
    "region_forest": f'(way["landuse"="forest"]{bb(REGION)};way["natural"="wood"]{bb(REGION)};'
                     f'relation["landuse"="forest"]{bb(REGION)};relation["natural"="wood"]{bb(REGION)};);',
    "region_places": f'node["place"~"^(city|town|village|suburb)$"]{bb(REGION)};',
    "region_roads": f'way["highway"~"^(motorway|trunk|primary)$"]{bb(REGION)};',
    "region_urban": f'way["landuse"~"^(residential|commercial|industrial|retail)$"]{bb(REGION)};',
    "city_coast": f'way["natural"="coastline"]{bb(CITY)};',
    "city_water": f'(way["natural"="water"]{bb(CITY)};relation["natural"="water"]{bb(CITY)};);',
    "city_green": f'(way["leisure"="park"]{bb(CITY)};relation["leisure"="park"]{bb(CITY)};'
                  f'way["landuse"~"^(grass|cemetery|recreation_ground)$"]{bb(CITY)};way["amenity"="grave_yard"]{bb(CITY)};);',
    "city_roads": f'way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|pedestrian|service)$"]{bb(CITY)};',
    "city_rail": f'way["railway"="rail"]{bb(CITY)};',
    "city_buildings": f'way["building"]{bb(INNER)};',
    "city_hospital": f'way["amenity"="hospital"]{bb(CITY)};',
    "city_teilum": 'way(id:25657593,89479450);',
}

def fetch(name, q):
    path = f"{OUT}/{name}.json"
    if os.path.exists(path): return
    for attempt in range(5):
        try:
            r = requests.post(API, data={"data": f"[out:json][timeout:180];{q}out geom;"}, headers={"User-Agent": UA}, timeout=240)
            if r.status_code == 200: break
            print(name, r.status_code, "retry")
        except requests.RequestException as e:
            print(name, "connection error, retry:", str(e)[:80])
        time.sleep(20 * (attempt + 1))
    r.raise_for_status()
    open(path, "w").write(r.text)
    print(name, len(r.json()["elements"]), "elements", flush=True)
    time.sleep(3)

if __name__ == "__main__":
    for k, q in QUERIES.items(): fetch(k, q)
    json.dump({"region": REGION, "city": CITY, "inner": INNER, "teilum": [C_LAT, C_LON],
               "source": "© OpenStreetMap contributors (ODbL), fetched " + time.strftime("%Y-%m-%d")},
              open(f"{OUT}/meta.json", "w"), indent=1)
