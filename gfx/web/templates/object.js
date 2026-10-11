// object — a modelled object on a dark table, lit like an evidence photograph: a slow
// turntable or push, one warm key light, one cold rim. Models are built from code
// (lathe profiles, displaced surfaces), so they read as models, never as archive photos.
import * as THREE from "../vendor/three.module.js";
const G = window.GFX;

function labelTexture(lines, colors) {
  const c = document.createElement("canvas");
  c.width = 2048; c.height = 1024;
  const x = c.getContext("2d");
  x.fillStyle = colors.bg; x.fillRect(0, 0, 2048, 1024);
  x.fillStyle = colors.band; x.fillRect(0, 610, 2048, 120);
  // label faces the camera between u = 0.25..0.75 of the lathe (front half)
  x.save(); x.translate(1024, 0);
  x.fillStyle = colors.fg; x.textAlign = "center";
  x.font = "700 92px Archivo"; x.fontStretch = "condensed";
  x.fillText(lines[0], 0, 380);
  x.font = "500 52px Archivo"; x.fillText(lines[1] || "", 0, 470);
  // GHS flame pictogram: red diamond, black flame
  x.translate(0, 820);
  x.save(); x.rotate(Math.PI / 4); x.fillStyle = "#fff"; x.fillRect(-70, -70, 140, 140);
  x.lineWidth = 14; x.strokeStyle = "#d0021b"; x.strokeRect(-70, -70, 140, 140); x.restore();
  x.fillStyle = "#111"; x.beginPath();
  x.moveTo(-30, 50); x.quadraticCurveTo(-48, 0, -10, -40); x.quadraticCurveTo(-8, -10, 6, -6);
  x.quadraticCurveTo(14, -40, 2, -66); x.quadraticCurveTo(48, -30, 34, 50); x.closePath(); x.fill();
  x.fillRect(-46, 52, 92, 10);
  x.restore();
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function bottle(p) {
  const g = new THREE.Group();
  const prof = [[0, 0], [0.036, 0], [0.04, 0.005], [0.041, 0.02], [0.041, 0.15], [0.038, 0.168], [0.024, 0.19], [0.015, 0.2],
    [0.015, 0.212]].map(([r, y]) => new THREE.Vector2(r, y));
  const bodyMat = new THREE.MeshPhysicalMaterial({ color: p.color || "#8a3424", roughness: 0.5, clearcoat: 0.25, clearcoatRoughness: 0.5 });
  const body = new THREE.Mesh(new THREE.LatheGeometry(prof, 96), bodyMat);
  g.add(body);
  // label sleeve
  const lab = new THREE.Mesh(new THREE.CylinderGeometry(0.0415, 0.0415, 0.11, 96, 1, true),
    new THREE.MeshStandardMaterial({ map: labelTexture(p.label || ["TÆNDVÆSKE", "1 liter"], { bg: "#d9d1bd", band: "#8a3424", fg: "#1b1b1b" }), roughness: 0.75 }));
  lab.position.y = 0.088; lab.rotation.y = Math.PI;
  g.add(lab);
  const capProf = [[0, 0.212], [0.017, 0.212], [0.0175, 0.236], [0.008, 0.24], [0.0035, 0.246], [0.003, 0.275], [0, 0.277]]
    .map(([r, y]) => new THREE.Vector2(r, y));
  g.add(new THREE.Mesh(new THREE.LatheGeometry(capProf, 64), new THREE.MeshStandardMaterial({ color: "#d9d3c4", roughness: 0.55 })));
  g.position.y = 0;
  return { group: g, target: new THREE.Vector3(0, 0.13, 0), dist: 0.62 };
}

function tread(u, v) {
  // a generic directional car-tyre tread: four circumferential grooves + chevron blocks
  const grooves = [0.2, 0.4, 0.6, 0.8].some((g) => Math.abs(v - g) < 0.022);
  const phase = (u * 38 + Math.abs(v - 0.5) * 3.2) % 1;
  const block = phase < 0.16 && v > 0.08 && v < 0.92;
  const sipe = (u * 38 * 3 + v * 7) % 1 < 0.05 && v > 0.2 && v < 0.8;
  return grooves || block ? 1 : sipe ? 0.45 : 0;
}

function cast(p) {
  const W = 0.62, H = 0.26;
  const geo = new THREE.PlaneGeometry(W, H, 520, 220);
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), y = pos.getY(i);
    const u = (x + W / 2) / W, v = (y + H / 2) / H;
    const inBand = v > 0.14 && v < 0.86;
    const vv = (v - 0.14) / 0.72;
    let z = 0.004 * (G.rand(i * 0.37) - 0.5) * 0.4;       // plaster grain
    if (inBand) {                                         // the tyre's ribs stand proud in the cast (4× supersampled)
      const du = 0.5 / 520, dv = 0.5 / 220 / 0.72;
      z += 0.0058 * (tread(u - du, vv - dv) + tread(u + du, vv - dv) + tread(u - du, vv + dv) + tread(u + du, vv + dv)) / 4;
    }
    const edge = Math.min(u, 1 - u, v, 1 - v);
    z *= G.clamp(edge * 25);
    z += 0.006 * G.clamp(edge * 8);                       // slab thickness rounding at the rim
    pos.setZ(i, z);
  }
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: "#a9a293", roughness: 0.97 }));
  m.rotation.x = -Math.PI / 2;
  const g = new THREE.Group();
  g.add(m);
  // a measuring stick beside it, like the technicians' photographs
  const stickTex = (() => {
    const c = document.createElement("canvas"); c.width = 2048; c.height = 64;
    const x = c.getContext("2d");
    for (let i = 0; i < 20; i++) { x.fillStyle = i % 2 ? "#111" : "#f2efe6"; x.fillRect(i * 102.4, 0, 102.4, 64); }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  })();
  const stick = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.004, 0.02), new THREE.MeshStandardMaterial({ map: stickTex, roughness: 0.6 }));
  stick.position.set(0, 0.002, H / 2 + 0.03);
  g.add(stick);
  return { group: g, target: new THREE.Vector3(0, 0, 0.01), dist: 0.75 };
}

G.register("object", {
  async setup(root, p, spec) {
    await document.fonts.load("700 150px Archivo");
    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.setSize(1920, 1080);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = p.exposure || 0.78;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    root.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#0c161c");
    scene.fog = new THREE.Fog("#0c161c", 1.2, 3.2);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), new THREE.MeshStandardMaterial({ color: "#0f1a20", roughness: 1 }));
    floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true;
    scene.add(floor);
    const model = (p.model === "cast" ? cast : bottle)(p);
    model.group.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(model.group);
    const key = new THREE.SpotLight("#ffb07a", p.key ?? 9, 0, Math.PI / 11, 0.85, 1.6);
    key.position.set(-0.6, 1.0, 0.55); key.target.position.copy(model.target);
    key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0004;
    scene.add(key, key.target);
    if (p.model === "cast") { key.position.set(-1.2, 0.28, 0.15); key.angle = Math.PI / 6; key.intensity = p.key ?? 12; }  // grazing light shows the tread
    const rim = new THREE.DirectionalLight("#8fb3d9", p.rim ?? (p.model === "cast" ? 0.35 : 0.9));
    rim.position.set(0.8, 0.6, -1.0);
    scene.add(rim);
    scene.add(new THREE.HemisphereLight("#2a3b45", "#05090c", 0.35));
    const cam = new THREE.PerspectiveCamera(p.fov || 28, 1920 / 1080, 0.01, 20);
    const over = G.el("div", "layer", root);
    if (spec.credit) G.el("div", "credit", over, G.esc(spec.credit));
    let cap = null, capLines = null;
    if (p.caption) {
      cap = G.el("div", "cap", over);
      if (p.caption.k) G.el("div", "k", cap, G.esc(p.caption.k));
      const h = G.el("div", "h", cap);
      h.style.fontSize = (p.caption.size || 72) + "px";
      capLines = G.lines(h, [].concat(p.caption.h || []));
      if (p.caption.s) cap.sEl = G.el("div", "s", cap, G.esc(p.caption.s));
    }
    const orbit = p.orbit || [{ at: 0, az: -25, el: 18, dist: 1 }, { at: spec.dur, az: 20, el: 14, dist: 0.9 }];
    return {
      frame(t) {
        const az = (G.kf(t, orbit.map((o) => ({ at: o.at, v: o.az }))) * Math.PI) / 180;
        const el = (G.kf(t, orbit.map((o) => ({ at: o.at, v: o.el }))) * Math.PI) / 180;
        const d = model.dist * G.kf(t, orbit.map((o) => ({ at: o.at, v: o.dist ?? 1 })));
        const tg = model.target.clone();
        if (p.shift) tg.x += p.shift;  // leave room for the caption
        cam.position.set(tg.x + d * Math.sin(az) * Math.cos(el), tg.y + d * Math.sin(el), tg.z + d * Math.cos(az) * Math.cos(el));
        cam.lookAt(tg);
        if (p.flicker) key.intensity = (p.key ?? 9) * (0.9 + 0.1 * Math.sin(t * 8.3) * Math.sin(t * 3.1 + 2));
        renderer.render(scene, cam);
        if (cap) {
          capLines(t, p.caption.at ?? 0.4);
          if (cap.sEl) G.show(cap.sEl, t, (p.caption.at ?? 0.4) + 0.6, p.caption.until);
          if (p.caption.until !== undefined) cap.style.opacity = 1 - G.seg(t, p.caption.until - 0.5, p.caption.until);
        }
      },
    };
  },
});
