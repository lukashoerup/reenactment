// The film's map style (MapLibre, OpenMapTiles schema). Used only to bake raster tiles
// once (tilegen.html); shots composite those tiles, so a map frame costs as little as text.
window.makeMapStyle = function (base, opts) {
  opts = opts || {};
  const C = {
    land: "#15242c", skov: "#1a2d27", field: "#17272c", resid: "#1b2a31", water: "#0a151b",
    road0: "#2c3b42", road1: "#3b4b53", road2: "#55646b", road3: "#6e7d83", rail: "#33434a",
    bldg: "#203139", border: "#56666d",
  };
  const W = (stops) => ["interpolate", ["exponential", 1.6], ["zoom"], ...stops];
  const cls = (list) => ["match", ["get", "class"], list, true, false];
  return {
    version: 8,
    sources: { v: { type: "vector", tiles: [base + "/tiles/vec/{z}/{x}/{y}.pbf"], maxzoom: 14 } },
    layers: [
      { id: "bg", type: "background", paint: { "background-color": C.land } },
      { id: "lc-wood", type: "fill", source: "v", "source-layer": "landcover", filter: cls(["wood", "forest"]),
        paint: { "fill-color": C.skov } },
      { id: "lc-field", type: "fill", source: "v", "source-layer": "landcover", filter: cls(["farmland", "grass", "wetland"]),
        paint: { "fill-color": C.field } },
      { id: "lu-res", type: "fill", source: "v", "source-layer": "landuse", minzoom: 8,
        filter: cls(["residential", "suburb", "neighbourhood", "industrial", "commercial"]), paint: { "fill-color": C.resid } },
      { id: "park", type: "fill", source: "v", "source-layer": "park", paint: { "fill-color": C.skov, "fill-opacity": 0.8 } },
      { id: "water", type: "fill", source: "v", "source-layer": "water", paint: { "fill-color": C.water } },
      { id: "waterway", type: "line", source: "v", "source-layer": "waterway", minzoom: 9,
        paint: { "line-color": C.water, "line-width": W([9, 0.6, 16, 4]) } },
      { id: "bldg", type: "fill", source: "v", "source-layer": "building", minzoom: 13,
        paint: { "fill-color": C.bldg, "fill-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0, 14.5, 1] } },
      { id: "path", type: "line", source: "v", "source-layer": "transportation", minzoom: 12,
        filter: cls(["path", "track"]), paint: { "line-color": C.road1, "line-dasharray": [2, 1.6], "line-width": W([12, 0.6, 18, 2.4]) } },
      { id: "rail", type: "line", source: "v", "source-layer": "transportation", minzoom: 8, filter: cls(["rail"]),
        paint: { "line-color": C.rail, "line-dasharray": [3, 2], "line-width": W([8, 0.6, 16, 2]) } },
      { id: "minor", type: "line", source: "v", "source-layer": "transportation", minzoom: 11,
        filter: cls(["minor", "service"]), paint: { "line-color": C.road0, "line-width": W([11, 0.5, 18, 9]) } },
      { id: "mid", type: "line", source: "v", "source-layer": "transportation", minzoom: 8,
        filter: cls(["secondary", "tertiary"]), paint: { "line-color": C.road1, "line-width": W([8, 0.5, 18, 14]) } },
      { id: "major", type: "line", source: "v", "source-layer": "transportation", minzoom: 5,
        filter: cls(["primary", "trunk"]), paint: { "line-color": C.road2, "line-width": W([5, 0.4, 18, 18]) } },
      { id: "mway", type: "line", source: "v", "source-layer": "transportation", minzoom: 5,
        filter: cls(["motorway"]), paint: { "line-color": C.road3, "line-width": W([5, 0.6, 18, 22]) } },
      { id: "border", type: "line", source: "v", "source-layer": "boundary", filter: ["==", ["get", "admin_level"], 2],
        paint: { "line-color": C.border, "line-dasharray": [3, 2], "line-width": 1.2 } },
    ],
  };
};
window.MAP_LAND = "#15242c";
