// map — the backbone template. Real geography (OpenStreetMap via OpenFreeMap vector tiles,
// optional aerial imagery) in the film's night palette. The style is baked once into
// raster tiles (gfx/maptiles.py); each frame composites those tiles on a canvas with a
// van Wijk "fly" camera and trilinear zoom, so map frames cost as little as text frames.
// Overlays (markers, routes, rings, areas, place names, caption) are SVG/HTML in the
// film's typography, projected with the same camera.
(function () {
  const G = GFX;
  const TS = 512;
  const W = 1920, H = 1080;
  const merc = ([lon, lat]) => {
    const s = Math.sin((lat * Math.PI) / 180);
    return [(lon + 180) / 360, 0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)];
  };
  const unmerc = ([x, y]) => [x * 360 - 180, (360 / Math.PI) * Math.atan(Math.exp((1 - 2 * y) * Math.PI)) - 90];

  // ----- camera: van Wijk & Nuij smooth zoom-pan (as MapLibre's flyTo) -----
  function flyPath(a, b) {
    const rho = 1.42, rho2 = rho * rho;
    const from = merc(a.center), to = merc(b.center);
    const ws = TS * Math.pow(2, a.zoom);
    const u1 = Math.hypot((to[0] - from[0]) * ws, (to[1] - from[1]) * ws);
    const w0 = Math.max(W, H), w1 = w0 / Math.pow(2, b.zoom - a.zoom);
    let S, u, w;
    const r = (i) => {
      const bb = (w1 * w1 - w0 * w0 + (i ? -1 : 1) * rho2 * rho2 * u1 * u1) / (2 * (i ? w1 : w0) * rho2 * u1);
      return Math.log(Math.sqrt(bb * bb + 1) - bb);
    };
    if (u1 < 1e-6) {
      const k = w1 < w0 ? -1 : 1;
      S = Math.abs(Math.log(w1 / w0)) / rho || 1;
      u = () => 0; w = (s) => Math.exp(k * rho * s);
    } else {
      const r0 = r(0);
      S = (r(1) - r0) / rho;
      w = (s) => Math.cosh(r0) / Math.cosh(r0 + rho * s);
      u = (s) => (w0 * ((Math.cosh(r0) * Math.tanh(r0 + rho * s) - Math.sinh(r0)) / rho2)) / u1;
    }
    return (k) => {
      if (k >= 1) return { m: to, zoom: b.zoom };
      const s = k * S;
      return { m: [from[0] + (to[0] - from[0]) * u(s), from[1] + (to[1] - from[1]) * u(s)], zoom: a.zoom + Math.log2(1 / w(s)) };
    };
  }
  function makeCam(cam) {
    const paths = [];
    return (t) => {
      if (t <= cam[0].at) return { m: merc(cam[0].center), zoom: cam[0].zoom, bearing: cam[0].bearing || 0 };
      for (let i = 0; i < cam.length - 1; i++) {
        const a = cam[i], b = cam[i + 1];
        if (t <= b.at) {
          const k = G.ease[b.ease || "inOut"](G.seg(t, a.at, b.at));
          let pos;
          if (b.path === "linear" || Math.abs(b.zoom - a.zoom) < 0.05) {
            const fa = merc(a.center), fb = merc(b.center);
            pos = { m: [G.lerp(fa[0], fb[0], k), G.lerp(fa[1], fb[1], k)], zoom: G.lerp(a.zoom, b.zoom, k) };
          } else {
            paths[i] = paths[i] || flyPath(a, b);
            pos = paths[i](k);
          }
          return { ...pos, bearing: G.lerp(a.bearing || 0, b.bearing || 0, k) };
        }
      }
      const l = cam[cam.length - 1];
      return { m: merc(l.center), zoom: l.zoom, bearing: l.bearing || 0 };
    };
  }

  // ----- which tiles a camera state needs -----
  function visible(state, level, tsize) {
    const scale = Math.pow(2, state.zoom - level) * (TS / tsize);   // screen px per tile px
    const n = Math.pow(2, level) * (TS / tsize > 1 ? 1 : 1);
    const world = tsize * Math.pow(2, level);
    const cx = state.m[0] * world, cy = state.m[1] * world;
    const half = (Math.hypot(W, H) / 2) / scale;                     // covers any bearing
    const x0 = Math.floor((cx - half) / tsize), x1 = Math.floor((cx + half) / tsize);
    const y0 = Math.max(0, Math.floor((cy - half) / tsize)), y1 = Math.min(Math.pow(2, level) - 1, Math.floor((cy + half) / tsize));
    const out = [];
    for (let x = x0; x <= x1; x++) for (let y = y0; y <= y1; y++) out.push([level, ((x % n) + n) % n, y, x]);
    return { out, scale, cx, cy };
  }
  const levelsFor = (z) => { const L = Math.floor(z); return [L, L + 1]; };
  G.mapPlan = (p, dur) => {
    const cam = makeCam(p.cam);
    const base = new Set(), sat = new Set();
    const satOn = (t) => p.sat && G.kf(t, p.sat) > 0.001;
    for (let t = -0.5; t <= dur + 0.5; t += 0.1) {
      const st = cam(t);
      for (const L of levelsFor(st.zoom)) {
        if (L < 0 || L > 18) continue;
        visible(st, L, TS).out.forEach(([z, x, y]) => base.add(`${z}/${x}/${y}`));
        if (satOn(t)) visible(st, L + 1, 256).out.forEach(([z, x, y]) => sat.add(`${z}/${x}/${y}`));
      }
    }
    return { base: [...base], sat: [...sat] };
  };

  // ----- geometry -----
  const R = 6371008.8;
  const hav = (a, b) => {
    const k = Math.PI / 180, dLat = (b[1] - a[1]) * k, dLon = (b[0] - a[0]) * k;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * k) * Math.cos(b[1] * k) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  };
  function slice(coords, frac) {
    if (frac >= 1) return coords;
    const d = [0];
    for (let i = 1; i < coords.length; i++) d.push(d[i - 1] + hav(coords[i - 1], coords[i]));
    const target = d[d.length - 1] * Math.max(0, frac), out = [coords[0]];
    for (let i = 1; i < coords.length; i++) {
      if (d[i] >= target) {
        const q = (target - d[i - 1]) / (d[i] - d[i - 1] || 1);
        out.push([G.lerp(coords[i - 1][0], coords[i][0], q), G.lerp(coords[i - 1][1], coords[i][1], q)]);
        return out;
      }
      out.push(coords[i]);
    }
    return out;
  }
  function circle(center, radius, n = 120) {
    const pts = [], lat = (center[1] * Math.PI) / 180;
    for (let i = 0; i <= n; i++) {
      const a = (i / n) * Math.PI * 2;
      pts.push([center[0] + ((radius * Math.cos(a)) / (R * Math.cos(lat))) * (180 / Math.PI),
                center[1] + ((radius * Math.sin(a)) / R) * (180 / Math.PI)]);
    }
    return pts;
  }
  const colorOf = (n) => ({ glod: "#ff7a33", papir: "#e8e3d7", taage: "#8f9ca2", blaa: "#7fa7c9" }[n] || n || "#e8e3d7");
  const NS = "http://www.w3.org/2000/svg";
  const S = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };

  G.register("map", {
    async setup(root, p, spec) {
      const canvas = G.el("canvas", "layer", root);
      canvas.width = W; canvas.height = H;
      const ctx = canvas.getContext("2d");
      const svg = S("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}` }, root);
      svg.style.position = "absolute"; svg.style.left = 0; svg.style.top = 0;
      const over = G.el("div", "layer", root);
      const cam = makeCam(p.cam);

      // preload every tile this shot will touch
      const plan = G.mapPlan(p, spec.dur);
      const imgs = new Map();
      const load = (key, url) => new Promise((res) => {
        const im = new Image();
        im.onload = () => { imgs.set(key, im); res(); };
        im.onerror = () => res();
        im.src = url;
      });
      await Promise.all([
        ...plan.base.map((k) => load("b/" + k, `${spec.base}/maptile/${spec.tilekey}/${k}.png`)),
        ...plan.sat.map((k) => load("s/" + k, `${spec.base}/tiles/sat/${k}.jpg`)),
      ]);

      // projection for the current frame
      let st = cam(0);
      const project = (ll) => {
        const ws = TS * Math.pow(2, st.zoom), m = merc(ll);
        const dx = (m[0] - st.m[0]) * ws, dy = (m[1] - st.m[1]) * ws;
        const a = (-(st.bearing || 0) * Math.PI) / 180;
        return [W / 2 + dx * Math.cos(a) - dy * Math.sin(a), H / 2 + dx * Math.sin(a) + dy * Math.cos(a)];
      };
      const pts = (coords) => coords.map((c) => project(c).map((v) => v.toFixed(1)).join(",")).join(" ");

      function drawLevel(prefix, L, tsize, alpha) {
        const v = visible(st, L, tsize);
        ctx.globalAlpha = alpha;
        for (const [z, x, y, xu] of v.out) {
          const im = imgs.get(`${prefix}/${z}/${x}/${y}`);
          if (!im) continue;
          const sx = (xu * tsize - v.cx) * v.scale, sy = (y * tsize - v.cy) * v.scale;
          const sz = tsize * v.scale;
          ctx.drawImage(im, sx - 0.5, sy - 0.5, sz + 1, sz + 1);   // +1 px overlap hides seams
        }
        ctx.globalAlpha = 1;
      }

      const routes = (p.routes || []).map((rt) => {
        const g = S("g", {}, svg);
        const casing = rt.casing === false ? null : S("polyline", { fill: "none", stroke: "#0b141a", "stroke-opacity": 0.7,
          "stroke-width": (rt.width || 5) + 6, "stroke-linecap": "round", "stroke-linejoin": "round" }, g);
        const line = S("polyline", { fill: "none", stroke: colorOf(rt.color), "stroke-width": rt.width || 5, "stroke-linecap": "round",
          "stroke-linejoin": "round", ...(rt.dash ? { "stroke-dasharray": rt.dash.map((d) => d * (rt.width || 5)).join(" ") } : {}) }, g);
        const head = rt.head === false ? null : G.el("div", "mk", over, `<div class="mk-dot" style="background:${colorOf(rt.color)}"></div>`);
        const lab = rt.label ? G.el("div", "mk", over, `<div class="t-small" style="position:absolute;white-space:nowrap;transform:translate(16px,-50%);color:${colorOf(rt.color)};font-size:30px;text-shadow:0 2px 12px #0b141a">${G.esc(rt.label)}</div>`) : null;
        return { rt, g, casing, line, head, lab };
      });
      const rings = (p.rings || []).map((rg) => {
        const g = S("g", {}, svg);
        const poly = S("polygon", { fill: colorOf(rg.color || "glod"), "fill-opacity": 0, stroke: colorOf(rg.color || "glod"),
          "stroke-width": rg.width || 2.5, ...(rg.dash ? { "stroke-dasharray": rg.dash.map((d) => d * 5).join(" ") } : {}) }, g);
        const lab = rg.label ? G.el("div", "mk", over, `<div class="t-small" style="color:${colorOf(rg.color || "glod")};white-space:nowrap;transform:translate(-50%,-130%)">${G.esc(rg.label)}</div>`) : null;
        return { rg, g, poly, lab };
      });
      const areas = (p.areas || []).map((ar) => {
        const poly = S("polygon", { fill: colorOf(ar.color || "glod"), "fill-opacity": 0, stroke: colorOf(ar.color || "glod"),
          "stroke-width": 2, "stroke-dasharray": "10 10" }, svg);
        return { ar, poly };
      });
      const places = (p.places || []).map((pl) => ({ pl, e: G.el("div", "place " + (pl.cls || ""), over, G.esc(pl.name)) }));
      const markers = (p.markers || []).map((m) => {
        const box = G.el("div", "mk", over);
        const halos = m.kind === "ember" ? [0, 1, 2].map(() => G.el("div", "mk-halo", box)) : [];
        const dot = G.el("div", m.kind === "ember" ? "mk-ember" : "mk-dot", box);
        const leader = m.label ? G.el("div", "leader", box) : null;
        const lab = m.label ? G.el("div", "mk-label" + (m.kind === "ember" ? " hot" : ""), box,
          `<div class="name">${G.esc(m.label)}</div>${m.sub ? `<div class="sub">${G.esc(m.sub)}</div>` : ""}`) : null;
        return { m, box, dot, halos, leader, lab };
      });
      let cap = null, capLines = null;
      if (p.caption) {
        cap = G.el("div", "cap", over);
        if (p.caption.k) cap.kEl = G.el("div", "k", cap, G.esc(p.caption.k));
        const h = G.el("div", "h", cap);
        capLines = G.lines(h, [].concat(p.caption.h || []));
        if (p.caption.s) cap.sEl = G.el("div", "s", cap, G.esc(p.caption.s));
      }
      if (spec.credit) G.el("div", "credit", over, G.esc(spec.credit));

      return {
        frame(t) {
          st = cam(t);
          ctx.setTransform(1, 0, 0, 1, 0, 0);
          ctx.fillStyle = "#15242c";
          ctx.fillRect(0, 0, W, H);
          ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = "high";
          ctx.translate(W / 2, H / 2);
          ctx.rotate((-(st.bearing || 0) * Math.PI) / 180);
          // trilinear zoom: level L scaled up, level L+1 scaled down, blended by the fraction
          const L = Math.floor(st.zoom), f = st.zoom - L;
          drawLevel("b", L, TS, 1);
          if (f > 0.001) drawLevel("b", L + 1, TS, G.ease.inOutSine(f));
          const so = p.sat ? G.kf(t, p.sat) : 0;
          if (so > 0.001) {
            ctx.filter = p.sat_filter || "saturate(0.45) brightness(0.62) contrast(1.08)";
            drawLevel("s", L + 1, 256, so);
            if (f > 0.001) drawLevel("s", L + 2, 256, so * G.ease.inOutSine(f));
            ctx.filter = "none";
          }
          ctx.setTransform(1, 0, 0, 1, 0, 0);

          for (const r of routes) {
            const rt = r.rt;
            const k = G.ease[rt.ease || "inOutSine"](G.seg(t, rt.at ?? 0, rt.until ?? (rt.at ?? 0) + 2));
            const part = slice(rt.coords, Math.max(k, 0.0005));
            const P = pts(part);
            r.line.setAttribute("points", P);
            if (r.casing) r.casing.setAttribute("points", P);
            const o = (t < (rt.at ?? 0) ? 0 : 1) * (rt.out !== undefined ? 1 - G.seg(t, rt.out, rt.out + 0.6) : 1);
            r.g.style.opacity = o;
            const end = project(part[part.length - 1]);
            if (r.head) { r.head.style.transform = `translate(${end[0]}px,${end[1]}px)`; r.head.style.opacity = k > 0 && k < 1 ? o : 0; }
            if (r.lab) { r.lab.style.transform = `translate(${end[0]}px,${end[1]}px)`; r.lab.style.opacity = o * G.seg(t, (rt.until ?? 0) - 0.3, (rt.until ?? 0) + 0.3); }
          }
          for (const r of rings) {
            const rg = r.rg;
            const k = G.ease.outExpo(G.seg(t, rg.at ?? 0, (rg.at ?? 0) + (rg.grow || 1.6)));
            const rad = Math.max(1, rg.radius * k);
            r.poly.setAttribute("points", pts(circle(rg.center, rad)));
            const o = (t >= (rg.at ?? 0) ? 1 : 0) * (rg.until !== undefined ? 1 - G.seg(t, rg.until - 0.5, rg.until) : 1);
            r.g.style.opacity = o;
            r.poly.setAttribute("fill-opacity", rg.fill || 0);
            if (r.lab) {
              const top = project(circle(rg.center, rad, 4)[1]);
              r.lab.style.transform = `translate(${top[0]}px,${top[1]}px)`;
              r.lab.style.opacity = o * G.seg(t, (rg.at ?? 0) + 0.6, (rg.at ?? 0) + 1.2);
            }
          }
          for (const a of areas) {
            const ar = a.ar;
            const o = G.ease.out(G.seg(t, ar.at ?? 0, (ar.at ?? 0) + 0.8)) * (ar.until !== undefined ? 1 - G.seg(t, ar.until - 0.5, ar.until) : 1);
            a.poly.setAttribute("points", pts(ar.coords));
            a.poly.setAttribute("fill-opacity", (ar.fill ?? 0.12) * o);
            a.poly.style.opacity = o;
          }
          for (const { pl, e } of places) {
            const [x, y] = project(pl.ll);
            e.style.left = x + "px"; e.style.top = y + "px";
            G.show(e, t, pl.at, pl.until, 0.8, 0.6);
          }
          for (const { m, box, dot, halos, leader, lab } of markers) {
            const [x, y] = project(m.ll);
            box.style.transform = `translate(${x}px,${y}px)`;
            const at = m.at ?? -1;
            G.show(box, t, at, m.until, 0.35, 0.5);
            dot.style.transform = `scale(${0.3 + 0.7 * G.ease.out(G.seg(t, at, at + 0.5))})`;
            halos.forEach((h, i) => {
              const ph = (((t - at) / 2.4 + i / 3) % 1 + 1) % 1;
              const sz = 20 + ph * 120;
              h.style.width = h.style.height = sz + "px";
              h.style.margin = `${-sz / 2}px 0 0 ${-sz / 2}px`;
              h.style.opacity = t < at ? 0 : (1 - ph) * 0.55;
            });
            if (lab) {
              const len = m.leader ?? 70;
              const ang = { right: -30, left: 210, up: -90, down: 90 }[m.side || "right"] ?? m.side;
              const lp = G.ease.out(G.seg(t, at + 0.25, at + 0.8));
              leader.style.width = len * lp + "px";
              leader.style.transform = `rotate(${ang}deg)`;
              const ex = Math.cos((ang * Math.PI) / 180) * len, ey = Math.sin((ang * Math.PI) / 180) * len;
              const left = Math.cos((ang * Math.PI) / 180) < -0.1, vert = Math.abs(Math.cos((ang * Math.PI) / 180)) < 0.1;
              lab.style.left = ex + (vert ? 0 : left ? -12 : 12) + "px";
              lab.style.top = ey + (vert ? (ey < 0 ? -12 : 12) : 0) + "px";
              lab.style.transform = vert ? `translate(-50%, ${ey < 0 ? "-100%" : "0"})` : `translate(${left ? "-100%" : "0"}, -50%)`;
              lab.style.textAlign = vert ? "center" : left ? "right" : "left";
              lab.style.opacity = G.ease.out(G.seg(t, at + 0.5, at + 1.0));
            }
          }
          if (cap) {
            const c = p.caption, at = c.at ?? 0.3;
            capLines(t, at);
            if (cap.kEl) cap.kEl.style.opacity = G.ease.out(G.seg(t, at - 0.2, at + 0.4));
            cap.style.opacity = c.until !== undefined ? 1 - G.seg(t, c.until - 0.5, c.until) : 1;
            if (cap.sEl) cap.sEl.style.opacity = G.ease.out(G.seg(t, at + 0.5, at + 1.1));
          }
        },
      };
    },
  });
})();
