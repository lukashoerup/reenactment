// @render-version 09993cc8f0
// (Cache key for shots of this template. Bump it whenever an edit changes what existing
// shots look like; opt-in parameters whose defaults keep the old look need no bump.)
// diorama — the find site as a 3D miniature: a forest clearing at night in the rain, the
// bonfire, the road, the tracks. One set, re-used across the whole episode, the way
// documentary channels like Fern return to a modelled location. Everything is built from
// code (no scans, no generated images); the layout comes from case.json's `site`
// (metres: x east, y south). Camera keyframes: [{at, pos:[x, height, y], look:[x, height, y], fov}].
import * as THREE from "../vendor/three.module.js";
const G = window.GFX;
const V = (p) => new THREE.Vector3(p[0], p[1], p[2]);           // [x, h, y] → three (x, y-up, z=south)
const P2 = (x, y, h = 0) => new THREE.Vector3(x, h, y);

// ---------- textures from canvas ----------
function canvasTex(w, h, draw, repeat) {
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  draw(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat, repeat); }
  t.anisotropy = 4;
  return t;
}
const radial = (stops) => canvasTex(128, 128, (x) => {
  const g = x.createRadialGradient(64, 64, 0, 64, 64, 64);
  stops.forEach(([o, c]) => g.addColorStop(o, c));
  x.fillStyle = g; x.fillRect(0, 0, 128, 128);
});
function forestFloor() {
  return canvasTex(1024, 1024, (x, w, h) => {
    x.fillStyle = "#3a4130"; x.fillRect(0, 0, w, h);
    const cols = ["#4b4a33", "#584631", "#2f3a28", "#405236", "#62553a", "#283022"];
    for (let i = 0; i < 9000; i++) {
      const r = 1 + G.rand(i * 3.1) * 6;
      x.fillStyle = cols[Math.floor(G.rand(i * 7.7) * cols.length)];
      x.globalAlpha = 0.35 + 0.5 * G.rand(i * 1.9);
      x.beginPath();
      x.ellipse(G.rand(i * 1.3) * w, G.rand(i * 5.9) * h, r, r * (0.4 + G.rand(i * 2.3)), G.rand(i) * 3, 0, Math.PI * 2);
      x.fill();
    }
    x.globalAlpha = 1;
  }, 24);
}
function mudTex() {
  return canvasTex(512, 512, (x, w, h) => {
    x.fillStyle = "#3a3127"; x.fillRect(0, 0, w, h);
    for (let i = 0; i < 2500; i++) {
      x.fillStyle = G.rand(i * 4.3) > 0.5 ? "#332b22" : "#1f1b16";
      x.globalAlpha = 0.5;
      x.fillRect(G.rand(i * 1.7) * w, G.rand(i * 2.9) * h, 2 + G.rand(i) * 8, 1 + G.rand(i * 3.3) * 3);
    }
  }, 1);
}

// ---------- geometry helpers ----------
function smoothPath(points, step = 0.5) {
  const curve = new THREE.CatmullRomCurve3(points.map(([x, y]) => P2(x, y)), false, "centripetal");
  const n = Math.max(2, Math.ceil(curve.getLength() / step));
  return curve.getSpacedPoints(n);
}
function ribbon(pts, width, offset = 0, y = 0.02) {
  // a flat strip along pts (Vector3 on ground), `offset` metres to the side
  const pos = [], idx = [], uv = [];
  let along = 0;
  for (let i = 0; i < pts.length; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
    const d = new THREE.Vector3().subVectors(b, a).setY(0).normalize();
    const nx = -d.z, nz = d.x;
    if (i > 0) along += pts[i].distanceTo(pts[i - 1]);
    for (const s of [-1, 1]) {
      const o = offset + (s * width) / 2;
      pos.push(pts[i].x + nx * o, y, pts[i].z + nz * o);
      uv.push(s < 0 ? 0 : 1, along / 4);
    }
    if (i > 0) { const k = i * 2; idx.push(k - 2, k - 1, k, k - 1, k + 1, k); }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}
function distToPolyline(x, z, pts) {
  let best = 1e9;
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i];
    const dx = b.x - a.x, dz = b.z - a.z, L = dx * dx + dz * dz || 1;
    const t = Math.max(0, Math.min(1, ((x - a.x) * dx + (z - a.z) * dz) / L));
    best = Math.min(best, Math.hypot(x - a.x - t * dx, z - a.z - t * dz));
  }
  return best;
}

// ---------- flame shader ----------
const FLAME_FRAG = `
uniform float uTime; uniform float uIntensity; uniform float uSeed; varying vec2 vUv;
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
  return mix(mix(hash(i), hash(i+vec2(1.0,0.0)), f.x), mix(hash(i+vec2(0.0,1.0)), hash(i+vec2(1.0,1.0)), f.x), f.y); }
float fbm(vec2 p){ float v = 0.0, a = 0.5; for (int i = 0; i < 5; i++){ v += a*noise(p); p *= 2.03; a *= 0.5; } return v; }
void main(){
  vec2 uv = vUv;
  float n = fbm(vec2(uv.x*3.2 + uSeed, uv.y*2.4 - uTime*1.7));
  float n2 = fbm(vec2(uv.x*6.0 - uSeed, uv.y*5.0 - uTime*2.6));
  float shape = 1.0 - pow(abs(uv.x - 0.5) * 2.0, 1.6);
  shape *= smoothstep(0.0, 0.12, uv.y);
  float f = shape * (1.05 - uv.y) * 1.35 + (n - 0.5) * 0.95 + (n2 - 0.5) * 0.35;
  f = smoothstep(0.28, 0.78, f) * uIntensity;
  vec3 col = mix(vec3(0.75, 0.12, 0.02), vec3(1.0, 0.55, 0.12), smoothstep(0.25, 0.7, f));
  col = mix(col, vec3(1.0, 0.92, 0.7), smoothstep(0.75, 1.0, f));
  gl_FragColor = vec4(col * f * 1.25, f);
}`;
const FLAME_VERT = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;

// ---------- models ----------
function makeTrees(scene, p, avoid) {
  const ext = p.trees_extent || 85;
  const n = p.trees || 520;
  const spruceTrunk = new THREE.CylinderGeometry(0.12, 0.2, 2.2, 6); spruceTrunk.translate(0, 1.1, 0);
  const spruceCrown = new THREE.ConeGeometry(1.6, 7.5, 8, 3); spruceCrown.translate(0, 5.6, 0);
  const beechTrunk = new THREE.CylinderGeometry(0.16, 0.26, 5.5, 6); beechTrunk.translate(0, 2.75, 0);
  const beechCrown = new THREE.IcosahedronGeometry(2.8, 1); beechCrown.scale(1, 0.85, 1); beechCrown.translate(0, 7.2, 0);
  const trunkMat = new THREE.MeshStandardMaterial({ color: "#43362a", roughness: 1, flatShading: true });
  const needleMat = new THREE.MeshStandardMaterial({ color: "#2d4636", roughness: 0.95, flatShading: true });
  const leafMat = new THREE.MeshStandardMaterial({ color: "#5f6a3a", roughness: 0.95, flatShading: true });
  const spots = [];
  for (let i = 0; i < n * 4 && spots.length < n; i++) {
    const x = (G.rand(i * 2.71 + 0.3) * 2 - 1) * ext, z = (G.rand(i * 3.97 + 1.1) * 2 - 1) * ext;
    if (avoid(x, z)) continue;
    if (spots.some((s) => Math.hypot(s.x - x, s.z - z) < 2.6)) continue;
    spots.push({ x, z, k: G.rand(i * 5.3), s: 0.75 + 0.6 * G.rand(i * 7.1), r: G.rand(i * 9.9) * 6.28 });
  }
  const spruce = spots.filter((s) => s.k < 0.6), beech = spots.filter((s) => s.k >= 0.6);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), c = new THREE.Color();
  for (const [list, trunk, crown, mat] of [[spruce, spruceTrunk, spruceCrown, needleMat], [beech, beechTrunk, beechCrown, leafMat]]) {
    const it = new THREE.InstancedMesh(trunk, trunkMat, list.length);
    const ic = new THREE.InstancedMesh(crown, mat, list.length);
    list.forEach((s, i) => {
      q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), s.r);
      m.compose(new THREE.Vector3(s.x, 0, s.z), q, new THREE.Vector3(s.s, s.s * (0.9 + 0.3 * G.rand(i)), s.s));
      it.setMatrixAt(i, m); ic.setMatrixAt(i, m);
      c.set(mat.color).multiplyScalar(0.75 + 0.5 * G.rand(i * 13.1));
      ic.setColorAt(i, c);
    });
    scene.add(it, ic);
  }
  return spots;
}

function makeFire(scene, x, z, burnt) {
  const g = new THREE.Group();
  g.position.set(x, 0, z);
  // burnt patch and stone ring
  const patch = new THREE.Mesh(new THREE.CircleGeometry(2.6, 40), new THREE.MeshStandardMaterial({ map: radial([[0, "#0b0907"], [0.65, "#141009"], [1, "rgba(20,16,10,0)"]]), transparent: true, roughness: 1, depthWrite: false }));
  patch.rotation.x = -Math.PI / 2; patch.position.y = 0.015; g.add(patch);
  const stoneMat = new THREE.MeshStandardMaterial({ color: "#4a4a44", roughness: 0.9, flatShading: true });
  for (let i = 0; i < 13; i++) {
    const a = (i / 13) * 6.283 + G.rand(i) * 0.2, s = new THREE.Mesh(new THREE.DodecahedronGeometry(0.18 + 0.08 * G.rand(i * 3), 0), stoneMat);
    s.position.set(Math.cos(a) * 1.45, 0.08, Math.sin(a) * 1.45); s.rotation.set(G.rand(i * 2), G.rand(i * 4), 0); g.add(s);
  }
  // logs: a stacked bonfire, built deliberately
  const logMat = new THREE.MeshStandardMaterial({ color: burnt ? "#0e0d0c" : "#1c140e", roughness: 0.95, emissive: "#ff5a14", emissiveIntensity: 0.0, flatShading: true });
  for (let i = 0; i < 10; i++) {
    const a = (i / 10) * 6.283;
    const len = (1.9 + 0.4 * G.rand(i)) * (burnt ? 0.55 : 1);
    const log = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.1, len, 6), logMat);
    const lean = burnt ? 1.15 + 0.3 * G.rand(i * 5) : 0.45;           // a burnt-out fire has collapsed
    const rr = burnt ? 0.5 + 0.4 * G.rand(i * 3) : 0.38;
    log.position.set(Math.cos(a) * rr, burnt ? 0.12 : 0.75, Math.sin(a) * rr);
    log.rotation.set(Math.sin(a) * lean, G.rand(i) * (burnt ? 1 : 0), -Math.cos(a) * lean);
    g.add(log);
  }
  for (let i = 0; i < 4; i++) {
    const log = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.11, 2.0, 6), logMat);
    log.rotation.set(0, (i / 4) * 3.14, Math.PI / 2); log.position.y = 0.12 + i * 0.07; g.add(log);
  }
  // flames: crossed planes with a noise shader
  const flames = [];
  for (let i = 0; i < 4; i++) {
    const mat = new THREE.ShaderMaterial({ vertexShader: FLAME_VERT, fragmentShader: FLAME_FRAG, transparent: true, depthWrite: false,
      blending: THREE.AdditiveBlending, side: THREE.DoubleSide, uniforms: { uTime: { value: 0 }, uIntensity: { value: 1 }, uSeed: { value: i * 3.7 } } });
    const pl = new THREE.Mesh(new THREE.PlaneGeometry(2.0, 3.0), mat);
    pl.geometry.translate(0, 1.5, 0);
    pl.rotation.y = (i / 4) * Math.PI;
    g.add(pl); flames.push(pl);
  }
  // embers
  const N = 260, emb = new Float32Array(N * 3);
  const embGeo = new THREE.BufferGeometry(); embGeo.setAttribute("position", new THREE.BufferAttribute(emb, 3));
  const embers = new THREE.Points(embGeo, new THREE.PointsMaterial({ size: 0.07, map: radial([[0, "#fff"], [0.3, "#ffb066"], [1, "rgba(255,120,40,0)"]]),
    color: "#ffae5c", transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true }));
  g.add(embers);
  // smoke
  const smokeTex = radial([[0, "rgba(255,255,255,0.55)"], [0.5, "rgba(255,255,255,0.18)"], [1, "rgba(255,255,255,0)"]]);
  const smoke = [];
  for (let i = 0; i < 36; i++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: smokeTex, color: "#7d8589", transparent: true, depthWrite: false, opacity: 0 }));
    g.add(s); smoke.push(s);
  }
  // glow halo (stands in for bloom)
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: radial([[0, "rgba(255,170,90,0.9)"], [0.25, "rgba(255,110,40,0.35)"], [1, "rgba(255,80,20,0)"]]),
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  glow.position.y = 1.0; glow.scale.set(9, 9, 1); g.add(glow);
  const light = new THREE.PointLight("#ff8a3d", 120, 0, 2); light.position.y = 1.4; g.add(light);
  scene.add(g);
  return {
    group: g,
    update(t, fire, smokeAmt, ember = 3) {
      const fl = 0.86 + 0.14 * Math.sin(t * 9.3) * Math.sin(t * 4.1 + 1.3) + 0.05 * Math.sin(t * 23.0);
      flames.forEach((f, i) => {
        f.material.uniforms.uTime.value = t + i * 0.37;
        f.material.uniforms.uIntensity.value = fire;
        f.scale.set(0.6 + 0.6 * fire, 0.35 + 0.85 * fire, 1);
        f.visible = fire > 0.02;
      });
      light.intensity = 140 * Math.max(0, fire) * fl + ember * smokeAmt;   // ember: what still glows in the ashes
      glow.material.opacity = Math.min(1, fire * 0.95) * fl;
      glow.scale.setScalar(5 + 6 * fire);
      logMat.emissiveIntensity = 0.04 * fire + (ember / 3) * 0.05 * Math.max(0, 0.6 - fire) * smokeAmt;   // embers glow faintly in the ashes
      for (let i = 0; i < N; i++) {
        const life = 2.2 + 1.8 * G.rand(i * 1.7), ph = ((t + G.rand(i * 3.3) * life) % life) / life;
        const r = 0.3 + 0.5 * G.rand(i * 2.1);
        emb[i * 3] = Math.cos(i * 2.4 + t * 0.6) * r * (1 - ph) + Math.sin(t * 1.3 + i) * 0.25 * ph;
        emb[i * 3 + 1] = 0.3 + ph * (2.5 + 3.5 * fire) * (0.7 + 0.6 * G.rand(i * 4.4));
        emb[i * 3 + 2] = Math.sin(i * 2.4 + t * 0.6) * r * (1 - ph) + Math.cos(t * 1.1 + i) * 0.25 * ph;
      }
      embGeo.attributes.position.needsUpdate = true;
      embers.material.opacity = Math.min(1, fire * 1.2);
      smoke.forEach((s, i) => {
        const life = 7 + 3 * G.rand(i * 5.1), ph = ((t + G.rand(i * 2.7) * life) % life) / life;
        s.position.set(Math.sin(i * 1.7) * 0.4 + ph * 2.2, 1.5 + ph * (6 + 4 * smokeAmt), Math.cos(i * 1.3) * 0.4 - ph * 0.8);
        const sc = 1.2 + ph * 5.5; s.scale.set(sc, sc, 1);
        s.material.opacity = Math.sin(ph * Math.PI) * 0.22 * smokeAmt;
      });
    },
  };
}

function makeCar(scene) {
  const g = new THREE.Group();
  const paint = new THREE.MeshStandardMaterial({ color: "#2b3036", roughness: 0.35, metalness: 0.4, flatShading: true });
  const glass = new THREE.MeshStandardMaterial({ color: "#0b1014", roughness: 0.15, metalness: 0.6 });
  const body = new THREE.Mesh(new THREE.BoxGeometry(3.9, 0.62, 1.68), paint); body.position.y = 0.6; g.add(body);
  // hatchback cabin: a wedge, steep at the back
  const cab = new THREE.BufferGeometry();
  const v = [[-1.75, 0, -0.78], [0.55, 0, -0.78], [-1.6, 0.56, -0.7], [-0.15, 0.58, -0.7], [-1.75, 0, 0.78], [0.55, 0, 0.78], [-1.6, 0.56, 0.7], [-0.15, 0.58, 0.7]];
  const f = [0, 2, 1, 1, 2, 3, 4, 5, 6, 5, 7, 6, 0, 4, 2, 2, 4, 6, 1, 3, 5, 3, 7, 5, 2, 6, 3, 3, 6, 7];
  cab.setAttribute("position", new THREE.Float32BufferAttribute(v.flat(), 3)); cab.setIndex(f); cab.computeVertexNormals();
  const cabin = new THREE.Mesh(cab, glass); cabin.position.y = 0.91; g.add(cabin);
  const wheelGeo = new THREE.CylinderGeometry(0.31, 0.31, 0.2, 14); wheelGeo.rotateX(Math.PI / 2);
  const tyre = new THREE.MeshStandardMaterial({ color: "#0d0d0d", roughness: 0.9 });
  for (const [wx, wz] of [[1.25, 0.78], [1.25, -0.78], [-1.25, 0.78], [-1.25, -0.78]]) { const w = new THREE.Mesh(wheelGeo, tyre); w.position.set(wx, 0.31, wz); g.add(w); }
  const headMat = new THREE.MeshBasicMaterial({ color: "#fff4d6" }), tailMat = new THREE.MeshBasicMaterial({ color: "#ff2a1a" });
  for (const s of [-1, 1]) {
    const h = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.14, 0.32), headMat); h.position.set(1.96, 0.72, s * 0.56); g.add(h);
    const tl = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.16, 0.22), tailMat); tl.position.set(-1.96, 0.74, s * 0.62); g.add(tl);
  }
  const beams = [];
  for (const s of [-1, 1]) {
    const sp = new THREE.SpotLight("#fff1d0", 260, 45, Math.PI / 7, 0.55, 1.6);
    sp.position.set(2.0, 0.72, s * 0.56); sp.target.position.set(12, -0.6, s * 0.8);
    g.add(sp, sp.target); beams.push(sp);
  }
  const red = new THREE.PointLight("#ff2a1a", 3, 8, 2); red.position.set(-2.2, 0.8, 0); g.add(red);
  scene.add(g);
  return g;
}

function marker(n) {
  const tex = canvasTex(256, 192, (x) => {
    x.fillStyle = "#f2c40f"; x.fillRect(0, 0, 256, 192);
    x.fillStyle = "#111"; x.font = "700 130px Archivo"; x.textAlign = "center"; x.textBaseline = "middle"; x.fillText(String(n), 128, 104);
  });
  const mat = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.6, side: THREE.DoubleSide });
  const g = new THREE.Group();
  for (const s of [-1, 1]) { const pl = new THREE.Mesh(new THREE.PlaneGeometry(0.28, 0.21), mat); pl.position.set(0, 0.09, s * 0.055); pl.rotation.x = s * 0.5; g.add(pl); }
  return g;
}

G.register("diorama", {
  async setup(root, p, spec) {
    await document.fonts.load("700 130px Archivo");
    const W = 1920, H = 1080;
    const renderer = new THREE.WebGLRenderer({ antialias: p.msaa ?? true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.setSize(W, H);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    root.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    // "overcast": the grey rainy day the episode describes (default); "night": for anything said to happen after dark
    const L = p.light === "night"
      ? { sky: "#17252e", fog: 0.022, hs: "#6a879a", hg: "#0e1211", hi: 1.15, sun: "#a9c0d6", si: 1.2, exp: 1.15 }
      : { sky: "#5b6a72", fog: 0.026, hs: "#b4c2ca", hg: "#2a2a24", hi: 1.25, sun: "#dfe6ea", si: 0.9, exp: 1.0 };
    renderer.toneMappingExposure = p.exposure ?? L.exp;
    const sky = new THREE.Color(p.sky || L.sky);
    scene.background = sky;
    scene.fog = new THREE.FogExp2(sky, p.fog ?? L.fog);
    scene.add(new THREE.HemisphereLight(L.hs, L.hg, p.ambient ?? L.hi));
    const moon = new THREE.DirectionalLight(L.sun, p.moon ?? L.si); moon.position.set(-30, 60, -10); scene.add(moon);

    const site = p.site || {};
    const roadPts = site.road ? smoothPath(site.road) : [];
    const pathPts = site.path ? smoothPath(site.path) : [];
    // ground
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(260, 260, 1, 1), new THREE.MeshStandardMaterial({ map: forestFloor(), roughness: 0.82, metalness: 0.05 }));
    ground.rotation.x = -Math.PI / 2; scene.add(ground);
    const clearing = new THREE.Mesh(new THREE.CircleGeometry(13, 48), new THREE.MeshStandardMaterial({ map: radial([[0, "#3d3327"], [0.7, "rgba(62,52,38,.8)"], [1, "rgba(58,62,46,0)"]]), transparent: true, roughness: 0.7, depthWrite: false }));
    clearing.rotation.x = -Math.PI / 2; clearing.position.y = 0.008; scene.add(clearing);
    if (roadPts.length) {
      const mud = new THREE.MeshStandardMaterial({ map: mudTex(), roughness: 0.55, metalness: 0.1, polygonOffset: true, polygonOffsetFactor: -1 });
      scene.add(new THREE.Mesh(ribbon(roadPts, 3.2, 0, 0.01), mud));
      const rut = new THREE.MeshStandardMaterial({ color: "#14110d", roughness: 0.25, metalness: 0.2, polygonOffset: true, polygonOffsetFactor: -2 });
      for (const o of [-0.72, 0.72]) scene.add(new THREE.Mesh(ribbon(roadPts, 0.32, o, 0.012), rut));
    }
    if (pathPts.length) {
      scene.add(new THREE.Mesh(ribbon(pathPts, 1.0, 0, 0.009), new THREE.MeshStandardMaterial({ color: "#2b261d", roughness: 0.9, polygonOffset: true, polygonOffsetFactor: -1 })));
    }
    const fire = site.fire || [0, 0];
    makeTrees(scene, p, (x, z) => Math.hypot(x - fire[0], z - fire[1]) < (p.clearing || 13)
      || (roadPts.length && distToPolyline(x, z, roadPts) < 3.4) || (pathPts.length && distToPolyline(x, z, pathPts) < 1.6));
    const burnt = p.burnt ?? (p.fire ? Math.max(...p.fire.map((k) => k.v)) < 0.01 : false);
    const bonfire = makeFire(scene, fire[0], fire[1], burnt);

    // rain: line segments in a box that follows the camera's target
    const RN = p.rain === 0 ? 0 : Math.round(3500 * (p.rain ?? 1));
    const rainPos = new Float32Array(RN * 6);
    const rainGeo = new THREE.BufferGeometry(); rainGeo.setAttribute("position", new THREE.BufferAttribute(rainPos, 3));
    const rain = new THREE.LineSegments(rainGeo, new THREE.LineBasicMaterial({ color: p.light === "night" ? "#9fb4c2" : "#dde6ea", transparent: true, opacity: p.light === "night" ? 0.32 : 0.28, depthWrite: false }));
    rain.frustumCulled = false; scene.add(rain);

    // ---------- items on a timeline ----------
    const items = [];
    const over = G.el("div", "layer", root);
    const labelEl = (it, hot) => {
      const box = G.el("div", "mk", over);
      const dot = G.el("div", "mk-dot", box);
      if (hot) dot.style.background = "var(--glod)";
      const leader = G.el("div", "leader", box);
      const lab = G.el("div", "mk-label" + (hot ? " hot" : ""), box,
        `<div class="name" style="font-size:${it.size || 42}px">${G.esc(it.text ?? it.label)}</div>${it.sub ? `<div class="sub">${G.esc(it.sub)}</div>` : ""}`);
      return { box, dot, leader, lab };
    };
    for (const it of p.items || []) {
      const rec = { it };
      if (it.type === "label") {
        Object.assign(rec, labelEl(it, it.hot));
      } else if (it.type === "text3d") {
        rec.el = G.el("div", "mk", over, `<div style="position:absolute;transform:translate(-50%,-50%);white-space:nowrap;text-align:center">` +
          `<div class="t-stamp" style="font-size:${it.size || 96}px;${it.hot ? "color:var(--glod);" : ""}text-shadow:0 0 2px rgba(5,10,14,.6),0 4px 34px rgba(5,10,14,.85),0 0 80px rgba(5,10,14,.55)">${G.esc(it.text)}</div>` +
          (it.sub ? `<div class="t-small" style="font-size:${Math.round((it.size || 96) * 0.36)}px;margin-top:10px;color:#c9cfd2;text-shadow:0 2px 16px #05090c">${G.esc(it.sub)}</div>` : "") + `</div>`);
      } else if (it.type === "ring") {
        const n = 72, gr = new THREE.Group(), w = it.width || Math.max(0.12, it.r * 0.012);
        const mat = new THREE.MeshBasicMaterial({ color: it.color === "papir" ? "#e8e3d7" : "#ff7a33", transparent: true, opacity: 0, depthWrite: false });
        for (let i = 0; i < n; i += 2) {
          const seg = new THREE.Mesh(new THREE.RingGeometry(it.r - w / 2, it.r + w / 2, 4, 1, (i / n) * 6.283, (6.283 / n) * 0.8), mat);
          seg.rotation.x = -Math.PI / 2; gr.add(seg);
        }
        gr.position.set(it.x ?? fire[0], 0.05, it.y ?? fire[1]); scene.add(gr);
        rec.obj = gr; rec.mat = mat;
      } else if (it.type === "tracks" || it.type === "steps") {
        const pts = smoothPath(it.points, 0.35);
        const mat = new THREE.MeshBasicMaterial({ color: it.color === "glod" ? "#ff7a33" : "#e8e3d7", transparent: true, opacity: 0, depthWrite: false });
        let geo;
        if (it.type === "tracks") {
          const a = ribbon(pts, it.width || 0.1, -(it.gauge || 1.45) / 2, 0.03), b = ribbon(pts, it.width || 0.1, (it.gauge || 1.45) / 2, 0.03);
          rec.objs = [new THREE.Mesh(a, mat), new THREE.Mesh(b, mat)];
          rec.counts = [a.index.count, b.index.count];
        } else {
          const dots = [];
          for (let i = 0; i < pts.length; i += 2) {
            const d = new THREE.Mesh(new THREE.CircleGeometry(0.09, 8), mat);
            const side = (i / 2) % 2 ? 0.14 : -0.14;
            const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
            const dir = new THREE.Vector3().subVectors(b, a).normalize();
            d.position.set(pts[i].x - dir.z * side, 0.03, pts[i].z + dir.x * side); d.rotation.x = -Math.PI / 2; d.scale.set(1, 1.6, 1);
            dots.push(d);
          }
          rec.objs = dots;
        }
        rec.objs.forEach((o) => scene.add(o));
        rec.mat = mat;
        if (it.label) Object.assign(rec, labelEl(it, it.color === "glod"));
        rec.anchor = it.lpos ? V(it.lpos) : pts[Math.floor(pts.length * 0.55)].clone().setY(0.3);
      } else if (it.type === "markers") {
        rec.objs = it.at_each.map(([x, y, n, at]) => { const m = marker(n); m.position.set(x, 0, y); m.rotation.y = G.rand(x * 3 + y) * 6; m.scale.setScalar(0.001); scene.add(m); return { m, at }; });
      } else if (it.type === "tape") {
        const tex = canvasTex(256, 32, (x) => { for (let i = 0; i < 8; i++) { x.fillStyle = i % 2 ? "#f4f1ea" : "#d01f1f"; x.fillRect(i * 32, 0, 32, 32); } });
        tex.wrapS = THREE.RepeatWrapping;
        const pts = it.points.map(([x, y]) => P2(x, y, it.height || 1.0));
        rec.objs = [];
        for (let i = 0; i < pts.length; i++) {
          const a = pts[i], b = pts[(i + 1) % pts.length];
          if (!it.closed && i === pts.length - 1) break;
          const L = a.distanceTo(b), t2 = tex.clone(); t2.needsUpdate = true; t2.repeat.set(L / 1.6, 1);
          const strip = new THREE.Mesh(new THREE.PlaneGeometry(L, 0.08), new THREE.MeshStandardMaterial({ map: t2, side: THREE.DoubleSide, roughness: 0.5, transparent: true, opacity: 0 }));
          strip.position.copy(a).lerp(b, 0.5); strip.rotation.y = -Math.atan2(b.z - a.z, b.x - a.x);
          scene.add(strip); rec.objs.push(strip);
          const post = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, (it.height || 1) + 0.1, 5), new THREE.MeshStandardMaterial({ color: "#3a3a36", transparent: true, opacity: 0 }));
          post.position.set(a.x, ((it.height || 1) + 0.1) / 2, a.z); scene.add(post); rec.objs.push(post);
        }
      } else if (it.type === "tarp") {
        const geo = new THREE.PlaneGeometry(it.w || 4.5, it.h || 4.5, 24, 24);
        const pos = geo.attributes.position;
        for (let i = 0; i < pos.count; i++) pos.setZ(i, 0.08 * Math.sin(pos.getX(i) * 3.1 + pos.getY(i) * 1.7) + 0.05 * G.rand(i));
        geo.computeVertexNormals();
        const tarp = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: "#35577a", roughness: 0.6, metalness: 0.05, transparent: true, opacity: 0, side: THREE.DoubleSide }));
        tarp.rotation.x = -Math.PI / 2; tarp.position.set(it.x ?? fire[0], it.lift ?? 2.0, it.y ?? fire[1]); scene.add(tarp);
        for (const [px, pz] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
          const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, it.lift ?? 2.0, 5), new THREE.MeshStandardMaterial({ color: "#6b6f70", transparent: true, opacity: 0 }));
          pole.position.set((it.x ?? fire[0]) + px * (it.w || 4.5) * 0.45, (it.lift ?? 2.0) / 2, (it.y ?? fire[1]) + pz * (it.h || 4.5) * 0.45); scene.add(pole); (rec.poles = rec.poles || []).push(pole);
        }
        rec.obj = tarp;
      } else if (it.type === "litter") {
        const [x0, y0, x1, y1] = it.box;
        const cols = ["#d9d4c8", "#9aa3a8", "#c9b37a", "#6f7b80", "#e8e3d7"];
        rec.objs = [];
        for (let i = 0; i < (it.n || 60); i++) {
          const k = G.rand(i * 7.3);
          const geo = k < 0.4 ? new THREE.BoxGeometry(0.16, 0.05, 0.1) : k < 0.75 ? new THREE.CylinderGeometry(0.035, 0.035, 0.22, 6) : new THREE.IcosahedronGeometry(0.08, 0);
          const o = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: cols[i % cols.length], roughness: 0.5, emissive: it.glow ? "#ff7a33" : "#000", emissiveIntensity: 0 }));
          o.position.set(G.lerp(x0, x1, G.rand(i * 1.9)), 0.04, G.lerp(y0, y1, G.rand(i * 2.7)));
          o.rotation.set(k < 0.75 && k >= 0.4 ? Math.PI / 2 : 0, G.rand(i) * 6, 0);
          o.scale.setScalar(0.001); scene.add(o);
          rec.objs.push({ o, at: (it.at ?? 0) + ((it.until ?? (it.at ?? 0) + 3) - (it.at ?? 0)) * G.rand(i * 4.1) });
        }
      } else if (it.type === "car") {
        rec.car = makeCar(scene);
        rec.pts = smoothPath(it.points, 0.3);
        rec.curve = new THREE.CatmullRomCurve3(rec.pts);
      } else if (it.type === "bottle") {
        const prof = [[0, 0], [0.035, 0], [0.04, 0.06], [0.03, 0.12], [0.012, 0.15], [0, 0.155]].map(([r, h]) => new THREE.Vector2(r, h));
        const b = new THREE.Mesh(new THREE.LatheGeometry(prof, 10), new THREE.MeshStandardMaterial({ color: "#1b1512", roughness: 0.6, flatShading: true }));
        b.position.set(it.x, 0.05, it.y); b.rotation.set(1.3, 0.4, 0.2); b.scale.set(1.3, 1, 0.8); scene.add(b);
      }
      items.push(rec);
    }
    // the caption (lower left), same as other templates
    let cap = null, capLines = null;
    if (p.caption) {
      cap = G.el("div", "cap", over);
      if (p.caption.k) cap.kEl = G.el("div", "k", cap, G.esc(p.caption.k));
      const h = G.el("div", "h", cap);
      h.style.fontSize = (p.caption.size || 76) + "px";
      capLines = G.lines(h, [].concat(p.caption.h || []));
      if (p.caption.s) cap.sEl = G.el("div", "s", cap, G.esc(p.caption.s));
    }
    G.el("div", "credit", over, G.esc(spec.credit || "Model af fundstedet, ikke målfast"));

    // ---------- camera ----------
    const cam = new THREE.PerspectiveCamera(p.cam[0].fov || 40, W / H, 0.1, 600);
    const keys = p.cam;
    const posCurve = keys.length > 2 ? new THREE.CatmullRomCurve3(keys.map((k) => V(k.pos)), false, "centripetal") : null;
    const lookCurve = keys.length > 2 ? new THREE.CatmullRomCurve3(keys.map((k) => V(k.look)), false, "centripetal") : null;
    const camAt = (t) => {
      const t0 = keys[0].at, t1 = keys[keys.length - 1].at;
      if (keys.length === 1) return { pos: V(keys[0].pos), look: V(keys[0].look), fov: keys[0].fov || 40 };
      const g = (p.cam_ease === "linear" ? G.ease.linear : G.ease.inOutSine)(G.seg(t, t0, t1));
      const T = t0 + g * (t1 - t0);
      let i = 0; while (i < keys.length - 2 && T > keys[i + 1].at) i++;
      const k = G.seg(T, keys[i].at, keys[i + 1].at);
      const u = (i + k) / (keys.length - 1);
      const pos = posCurve ? posCurve.getPoint(u) : V(keys[0].pos).lerp(V(keys[1].pos), k);
      const look = lookCurve ? lookCurve.getPoint(u) : V(keys[0].look).lerp(V(keys[1].look), k);
      return { pos, look, fov: G.lerp(keys[i].fov || 40, keys[i + 1].fov || 40, k) };
    };
    const project = (v) => {
      const q = v.clone().project(cam);
      return { x: (q.x * 0.5 + 0.5) * W, y: (-q.y * 0.5 + 0.5) * H, behind: q.z > 1, dist: cam.position.distanceTo(v) };
    };
    const showLabel = (rec, t, anchor, at, until) => {
      const it = rec.it;
      const pt = project(anchor);
      rec.box.style.transform = `translate(${pt.x}px,${pt.y}px)`;
      const o = G.show(rec.box, t, at, until, 0.35, 0.5) * (pt.behind ? 0 : 1);
      rec.box.style.opacity = o;
      const len = it.leader ?? 90, ang = { up: -90, right: -35, left: 215 }[it.side || "up"] ?? it.side;
      const lp = G.ease.out(G.seg(t, at + 0.2, at + 0.7));
      rec.leader.style.width = len * lp + "px";
      rec.leader.style.transform = `rotate(${ang}deg)`;
      const ex = Math.cos((ang * Math.PI) / 180) * len, ey = Math.sin((ang * Math.PI) / 180) * len;
      const vert = Math.abs(Math.cos((ang * Math.PI) / 180)) < 0.1, left = Math.cos((ang * Math.PI) / 180) < -0.1;
      rec.lab.style.left = ex + (vert ? 0 : left ? -12 : 12) + "px";
      rec.lab.style.top = ey + (vert ? -10 : 0) + "px";
      rec.lab.style.transform = vert ? "translate(-50%, -100%)" : `translate(${left ? "-100%" : "0"}, -50%)`;
      rec.lab.style.textAlign = vert ? "center" : left ? "right" : "left";
      rec.lab.style.opacity = G.ease.out(G.seg(t, at + 0.4, at + 0.9));
    };

    return {
      frame(t) {
        const c = camAt(t);
        const shake = p.shake ?? 0.03;
        cam.position.copy(c.pos).add(new THREE.Vector3(Math.sin(t * 1.3) * shake, Math.sin(t * 1.7 + 1) * shake * 0.6, Math.cos(t * 1.1) * shake));
        cam.fov = c.fov; cam.updateProjectionMatrix();
        cam.lookAt(c.look);
        cam.updateMatrixWorld();
        const fireAmt = p.fire ? G.kf(t, p.fire) : 1;
        const smokeAmt = p.smoke ? G.kf(t, p.smoke) : 0.6;
        bonfire.update(t, fireAmt, smokeAmt, p.ember ?? 3);
        // rain around the look target
        const rc = c.look;
        for (let i = 0; i < RN; i++) {
          const sp = 9 + 4 * G.rand(i * 1.1), Hh = 24;
          const y = Hh - ((t * sp + G.rand(i * 3.7) * Hh) % Hh);
          const x = rc.x + (G.rand(i * 5.3) - 0.5) * 50, z = rc.z + (G.rand(i * 7.9) - 0.5) * 50;
          rainPos.set([x, y, z, x + 0.05, y - 0.45, z + 0.02], i * 6);
        }
        rainGeo.attributes.position.needsUpdate = true;
        for (const rec of items) {
          const it = rec.it, at = it.at ?? 0;
          const o = (it.until !== undefined ? 1 - G.seg(t, it.until - 0.5, it.until) : 1) * G.ease.out(G.seg(t, at, at + 0.6));
          if (it.type === "label") showLabel(rec, t, V(it.pos), at, it.until);
          else if (it.type === "text3d") {
            const pt = project(V(it.pos));
            const s = Math.max(0.2, Math.min(2.2, (it.ref || 14) / pt.dist));
            rec.el.style.transform = `translate(${pt.x}px,${pt.y}px) scale(${s})`;
            rec.el.style.opacity = pt.behind ? 0 : o;
          } else if (it.type === "ring") {
            const k = G.ease.outExpo(G.seg(t, at, at + (it.grow || 1.4)));
            rec.obj.scale.set(Math.max(0.001, k), 1, Math.max(0.001, k));
            rec.mat.opacity = 0.9 * o;
          } else if (it.type === "tracks" || it.type === "steps") {
            const k = it.draw === false ? 1 : G.ease.inOutSine(G.seg(t, at, it.draw_until ?? at + (it.draw ?? 1.5)));
            if (it.type === "tracks") rec.objs.forEach((m, j) => m.geometry.setDrawRange(0, Math.floor((rec.counts[j] * k) / 6) * 6));
            else rec.objs.forEach((m, j) => (m.visible = j / rec.objs.length <= k));
            rec.mat.opacity = (it.opacity ?? 0.65) * o;
            if (rec.box) showLabel(rec, t, rec.anchor, it.label_at ?? at + 0.3, it.until);
          } else if (it.type === "markers") {
            rec.objs.forEach(({ m, at: a }) => m.scale.setScalar(Math.max(0.001, 1.6 * (1 + 1.6 * Math.pow(G.seg(t, a, a + 0.45) - 1, 3) + 0.6 * Math.pow(G.seg(t, a, a + 0.45) - 1, 2)) * (t >= a ? 1 : 0))));
          } else if (it.type === "tape") {
            const k = G.seg(t, at, at + 1.2);
            rec.objs.forEach((m, j) => { m.material.opacity = G.seg(k, j / rec.objs.length, j / rec.objs.length + 0.15); });
          } else if (it.type === "tarp") {
            rec.obj.material.opacity = o; rec.obj.position.y = (it.lift ?? 2.0) + (1 - o) * 2;
            (rec.poles || []).forEach((pl) => (pl.material.opacity = o));
          } else if (it.type === "litter") {
            rec.objs.forEach(({ o: m, at: a }) => {
              const k = G.ease.out(G.seg(t, a, a + 0.3));
              m.scale.setScalar(Math.max(0.001, k * (it.scale || 1.6)));
              if (it.glow) m.material.emissiveIntensity = 0.9 * G.seg(t, it.glow, it.glow + 0.6);
            });
          } else if (it.type === "car") {
            const k = (G.ease[it.ease || "inOutSine"])(G.seg(t, at, it.until ?? at + 4));
            const pos = rec.curve.getPointAt(Math.min(0.999, k)), ahead = rec.curve.getPointAt(Math.min(1, k + 0.001));
            rec.car.position.copy(pos);
            rec.car.rotation.y = -Math.atan2(ahead.z - pos.z, ahead.x - pos.x);
            rec.car.visible = t >= (it.show ?? at - 0.01) && (it.hide === undefined || t < it.hide);
          }
        }
        renderer.render(scene, cam);
        if (cap) {
          const cc = p.caption, a = cc.at ?? 0.4;
          capLines(t, a);
          if (cap.kEl) cap.kEl.style.opacity = G.ease.out(G.seg(t, a - 0.2, a + 0.4));
          if (cap.sEl) G.show(cap.sEl, t, a + 0.6, cc.until);
          cap.style.opacity = cc.until !== undefined ? 1 - G.seg(t, cc.until - 0.5, cc.until) : 1;
        }
      },
    };
  },
});
