// siteplan — a top-down plan of a place, in metres, drawn the way a crime-scene sketch is
// drawn: grid, trees, paths, the fire, tracks, search radius. It is clearly a drawing, never
// a photograph. Camera keyframes: [{at, x, y, zoom}] (zoom = screen px per metre).
(function () {
  const G = GFX;
  const NS = "http://www.w3.org/2000/svg";
  const S = (tag, attrs, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  };
  const dist = (a, b) => Math.hypot(b[0] - a[0], b[1] - a[1]);
  function slice(pts, frac) {
    if (frac >= 1) return pts;
    const d = [0];
    for (let i = 1; i < pts.length; i++) d.push(d[i - 1] + dist(pts[i - 1], pts[i]));
    const tgt = d[d.length - 1] * Math.max(0, frac);
    const out = [pts[0]];
    for (let i = 1; i < pts.length; i++) {
      if (d[i] >= tgt) {
        const k = (tgt - d[i - 1]) / (d[i] - d[i - 1] || 1);
        out.push([G.lerp(pts[i - 1][0], pts[i][0], k), G.lerp(pts[i - 1][1], pts[i][1], k)]);
        return out;
      }
      out.push(pts[i]);
    }
    return out;
  }
  function offset(pts, o) {
    return pts.map((p, i) => {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
      const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1;
      return [p[0] - (dy / L) * o, p[1] + (dx / L) * o];
    });
  }
  function resample(pts, step) {
    const out = [];
    let carry = 0;
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i], L = dist(a, b);
      for (let s = carry; s < L; s += step) out.push({ p: [G.lerp(a[0], b[0], s / L), G.lerp(a[1], b[1], s / L)], dir: [(b[0] - a[0]) / L, (b[1] - a[1]) / L] });
      carry = (carry - L) % step; if (carry < 0) carry += step;
    }
    return out;
  }
  const ptsAttr = (pts) => pts.map((p) => p[0].toFixed(3) + "," + p[1].toFixed(3)).join(" ");
  const col = (n) => ({ glod: "#ff7a33", papir: "#e8e3d7", taage: "#8f9ca2", vej: "#5f6f76", skov: "#2c4239" }[n] || n || "#e8e3d7");

  G.register("siteplan", {
    async setup(root, p) {
      const bg = G.el("div", "layer", root);
      bg.style.background = "#0e1a20";
      const svg = S("svg", { width: 1920, height: 1080, viewBox: "0 0 1920 1080" }, root);
      svg.style.position = "absolute";
      const defs = S("defs", {}, svg);
      const rg = S("radialGradient", { id: "fireg" }, defs);
      S("stop", { offset: "0%", "stop-color": "#fff1d6" }, rg);
      S("stop", { offset: "30%", "stop-color": "#ff7a33" }, rg);
      S("stop", { offset: "100%", "stop-color": "#ff7a33", "stop-opacity": 0 }, rg);
      const world = S("g", {}, svg);
      const over = G.el("div", "layer", root);
      const NSS = { "vector-effect": "non-scaling-stroke", fill: "none" };

      // grid: 1 m minor, 10 m major
      const gridG = S("g", {}, world);
      const ext = p.extent || [-200, -200, 200, 200];
      for (let x = Math.ceil(ext[0] / 5) * 5; x <= ext[2]; x += 5)
        S("line", { x1: x, y1: ext[1], x2: x, y2: ext[3], stroke: x % 25 === 0 ? "#22343c" : "#18272e", "stroke-width": 1, ...NSS }, gridG);
      for (let y = Math.ceil(ext[1] / 5) * 5; y <= ext[3]; y += 5)
        S("line", { x1: ext[0], y1: y, x2: ext[2], y2: y, stroke: y % 25 === 0 ? "#22343c" : "#18272e", "stroke-width": 1, ...NSS }, gridG);

      const items = (p.items || []).map((it, idx) => {
        const g = S("g", {}, world);
        const rec = { it, g };
        if (it.type === "trees") {
          const [x0, y0, x1, y1] = it.box;
          const n = it.n || 120;
          const clear = it.clear || []; // [[x,y,r]] keep open (the clearing, the road)
          for (let i = 0; i < n * 3 && g.childNodes.length < n * 2; i++) {
            const x = G.lerp(x0, x1, G.rand(idx * 1000 + i * 2.1)), y = G.lerp(y0, y1, G.rand(idx * 1000 + i * 3.7 + 0.5));
            if (clear.some(([cx, cy, r]) => Math.hypot(x - cx, y - cy) < r)) continue;
            const r = (it.r || 2.6) * (0.6 + 0.8 * G.rand(i * 5.3 + idx));
            S("circle", { cx: x, cy: y, r, stroke: "#34503f", "stroke-width": 1.3, "vector-effect": "non-scaling-stroke",
              fill: "#14241d", "fill-opacity": 0.55 }, g);
            S("circle", { cx: x, cy: y, r: 0.22, fill: "#46624f" }, g);
          }
        } else if (it.type === "road" || it.type === "path") {
          rec.pts = it.points;
          if (it.type === "road") {
            rec.fill = S("polyline", { stroke: "#1d2b31", "stroke-linecap": "round", "stroke-linejoin": "round", fill: "none" }, g);
            rec.a = S("polyline", { stroke: col(it.color || "#8a979c"), "stroke-width": 2.4, ...NSS }, g);
            rec.b = S("polyline", { stroke: col(it.color || "#8a979c"), "stroke-width": 2.4, ...NSS }, g);
            rec.w = it.width || 3;
          } else {
            rec.a = S("polyline", { stroke: col(it.color || "vej"), "stroke-width": 2.5, "stroke-dasharray": "10 8", ...NSS }, g);
          }
        } else if (it.type === "tracks") {
          rec.pts = it.points;
          rec.gw = it.gauge || 1.45;
          rec.l = S("polyline", { stroke: col(it.color || "papir"), "stroke-width": 3, ...NSS }, g);
          rec.r = S("polyline", { stroke: col(it.color || "papir"), "stroke-width": 3, ...NSS }, g);
          rec.ticks = S("path", { stroke: col(it.color || "papir"), "stroke-width": 1.6, "stroke-opacity": 0.8, ...NSS }, g);
        } else if (it.type === "steps") {
          rec.pts = it.points;
          rec.dots = S("path", { stroke: col(it.color || "taage"), "stroke-width": 5, "stroke-linecap": "round", ...NSS }, g);
        } else if (it.type === "fire") {
          rec.glow = S("circle", { cx: it.x, cy: it.y, r: (it.r || 1.5) * 2.6, fill: "url(#fireg)", opacity: 0.0 }, g);
          rec.halo = S("circle", { cx: it.x, cy: it.y, r: 1, fill: "url(#fireg)", opacity: 0.35 }, g);
          rec.core = S("circle", { cx: it.x, cy: it.y, r: it.r || 1.5, stroke: "#ff7a33", "stroke-width": 2.5, ...NSS }, g);
        } else if (it.type === "ring") {
          rec.c = S("circle", { cx: it.x, cy: it.y, r: 0.1, stroke: col(it.color || "glod"), "stroke-width": 2, "stroke-dasharray": "12 9", ...NSS }, g);
        } else if (it.type === "zone") {
          rec.c = S("polygon", { points: ptsAttr(it.points), stroke: col(it.color || "glod"), "stroke-width": 2.5, "stroke-dasharray": "16 10",
            fill: col(it.color || "glod"), "fill-opacity": 0.0, "vector-effect": "non-scaling-stroke" }, g);
        } else if (it.type === "scatter") {
          const [x0, y0, x1, y1] = it.box;
          rec.marks = [];
          for (let i = 0; i < (it.n || 40); i++) {
            const x = G.lerp(x0, x1, G.rand(idx * 77 + i * 1.7)), y = G.lerp(y0, y1, G.rand(idx * 91 + i * 2.9));
            const m = S("rect", { x: x - 0.25, y: y - 0.25, width: 0.5, height: 0.5, fill: col(it.color || "papir"), opacity: 0 }, g);
            rec.marks.push({ m, at: (it.at ?? 0) + ((it.until ?? (it.at ?? 0) + 3) - (it.at ?? 0)) * G.rand(i * 4.1 + idx) });
          }
        }
        if (it.label) {
          rec.lab = G.el("div", "mk", over, `<div class="mk-label${it.type === "fire" ? " hot" : ""}" style="position:absolute">` +
            `<div class="name" style="font-size:${it.lsize || 42}px">${G.esc(it.label)}</div>${it.sub ? `<div class="sub">${G.esc(it.sub)}</div>` : ""}</div>`);
        }
        return rec;
      });
      // words that pop up where things lie (e.g. the rubbish in the forest floor)
      const words = (p.words || []).map((w) => ({ w, e: G.el("div", "mk", over,
        `<div class="t-small" style="position:absolute;transform:translate(-50%,-50%);white-space:nowrap;font-size:${w.size || 34}px;color:${col(w.color || "papir")};text-shadow:0 2px 12px #0e1a20">${G.esc(w.text)}</div>`) }));
      let cap = null, capLines = null;
      if (p.caption) {
        cap = G.el("div", "cap", over);
        const h = G.el("div", "h", cap);
        h.style.fontSize = "64px";
        capLines = G.lines(h, [].concat(p.caption.h || []));
        if (p.caption.s) cap.sEl = G.el("div", "s", cap, G.esc(p.caption.s));
      }
      // scale bar + north arrow, bottom right
      const sb = G.el("div", "", over);
      Object.assign(sb.style, { position: "absolute", right: "128px", bottom: "92px", textAlign: "right" });
      const sbBar = G.el("div", "", sb);
      Object.assign(sbBar.style, { height: "10px", borderLeft: "2px solid #8f9ca2", borderRight: "2px solid #8f9ca2", borderBottom: "2px solid #8f9ca2", marginLeft: "auto" });
      const sbTxt = G.el("div", "t-small", sb);
      Object.assign(sbTxt.style, { fontSize: "24px", marginTop: "6px" });
      const north = G.el("div", "t-small", over, "N");
      Object.assign(north.style, { position: "absolute", right: "128px", top: "88px", fontSize: "30px", fontWeight: 600, borderBottom: "2px solid #8f9ca2", paddingBottom: "4px" });
      if (p.credit) G.el("div", "credit", over, G.esc(p.credit));

      const cam = p.cam || [{ at: 0, x: 0, y: 0, zoom: 20 }];
      return {
        frame(t) {
          const x = G.kf(t, cam.map((c) => ({ at: c.at, v: c.x, ease: c.ease })));
          const y = G.kf(t, cam.map((c) => ({ at: c.at, v: c.y, ease: c.ease })));
          const z = Math.exp(G.kf(t, cam.map((c) => ({ at: c.at, v: Math.log(c.zoom), ease: c.ease }))));
          const rot = G.kf(t, cam.map((c) => ({ at: c.at, v: c.rot || 0, ease: c.ease })));
          world.setAttribute("transform", `translate(960 540) rotate(${rot}) scale(${z}) translate(${-x} ${-y})`);
          const proj = (px, py) => {
            const a = (rot * Math.PI) / 180, dx = (px - x) * z, dy = (py - y) * z;
            return [960 + dx * Math.cos(a) - dy * Math.sin(a), 540 + dx * Math.sin(a) + dy * Math.cos(a)];
          };
          for (const r of items) {
            const it = r.it;
            const o = G.show(r.g, t, it.at, it.until, 0.6, 0.5);
            const k = it.draw === false ? 1 : G.ease.inOutSine(G.seg(t, it.at ?? 0, (it.draw_until ?? ((it.at ?? 0) + (it.draw ?? 1.5)))));
            if (it.type === "road") {
              const part = slice(r.pts, k);
              r.fill.setAttribute("points", ptsAttr(part));
              r.fill.setAttribute("stroke-width", r.w);
              r.a.setAttribute("points", ptsAttr(offset(part, r.w / 2)));
              r.b.setAttribute("points", ptsAttr(offset(part, -r.w / 2)));
            } else if (it.type === "path") {
              r.a.setAttribute("points", ptsAttr(slice(r.pts, k)));
            } else if (it.type === "tracks") {
              const part = slice(r.pts, k);
              const L = offset(part, r.gw / 2), Rr = offset(part, -r.gw / 2);
              r.l.setAttribute("points", ptsAttr(L));
              r.r.setAttribute("points", ptsAttr(Rr));
              let d = "";
              for (const side of [L, Rr]) for (const s of resample(side, 0.35)) {
                const nx = -s.dir[1] * 0.14, ny = s.dir[0] * 0.14;
                d += `M${(s.p[0] - nx).toFixed(2)},${(s.p[1] - ny).toFixed(2)}L${(s.p[0] + nx).toFixed(2)},${(s.p[1] + ny).toFixed(2)}`;
              }
              r.ticks.setAttribute("d", d);
            } else if (it.type === "steps") {
              const part = slice(r.pts, k);
              let d = "";
              resample(part, Math.max(it.step || 0.7, 14 / z)).forEach((s, i) => {
                const side = i % 2 ? 0.16 : -0.16;
                const px = s.p[0] - s.dir[1] * side, py = s.p[1] + s.dir[0] * side;
                d += `M${px.toFixed(2)},${py.toFixed(2)}l${(s.dir[0] * 0.01).toFixed(3)},${(s.dir[1] * 0.01).toFixed(3)}`;
              });
              r.dots.setAttribute("d", d);
            } else if (it.type === "fire") {
              const fl = 0.85 + 0.15 * Math.sin(t * 9.1) * Math.sin(t * 5.3 + 1);
              r.glow.setAttribute("opacity", (it.dim ?? 0.9) * fl);
              r.halo.setAttribute("r", 22 / z);   // keeps the fire visible as a point when zoomed far out
            } else if (it.type === "ring") {
              const kk = G.ease.outExpo(G.seg(t, it.at ?? 0, (it.at ?? 0) + (it.grow || 1.4)));
              r.c.setAttribute("r", Math.max(0.1, it.r * kk));
            } else if (it.type === "zone") {
              r.c.setAttribute("fill-opacity", 0.07 * G.seg(t, it.at ?? 0, (it.at ?? 0) + 1));
            } else if (it.type === "scatter") {
              r.marks.forEach((m) => m.m.setAttribute("opacity", G.seg(t, m.at, m.at + 0.25) * 0.9));
            }
            if (r.lab) {
              const lx = it.lx ?? (it.x ?? (r.pts ? r.pts[r.pts.length - 1][0] : 0));
              const ly = it.ly ?? (it.y ?? (r.pts ? r.pts[r.pts.length - 1][1] : 0));
              const [sx, sy] = proj(lx, ly);
              r.lab.style.transform = `translate(${sx}px,${sy}px)`;
              const inner = r.lab.firstChild;
              inner.style.transform = it.lalign === "left" ? "translate(-100%,-50%) translateX(-22px)" : it.lalign === "up" ? "translate(-50%,-130%)" : "translate(22px,-50%)";
              inner.style.textAlign = it.lalign === "left" ? "right" : "left";
              G.show(r.lab, t, (it.label_at ?? it.at ?? 0) + 0.3, it.until, 0.5);
            }
          }
          for (const { w, e } of words) {
            const [sx, sy] = proj(w.x, w.y);
            e.style.transform = `translate(${sx}px,${sy}px)`;
            G.show(e, t, w.at, w.until ?? p.words_until, 0.35, 0.5);
          }
          if (cap) {
            capLines(t, p.caption.at ?? 0.3);
            if (cap.sEl) G.show(cap.sEl, t, (p.caption.at ?? 0.3) + 0.6, p.caption.until);
            if (p.caption.until !== undefined) cap.style.opacity = 1 - G.seg(t, p.caption.until - 0.5, p.caption.until);
          }
          // scale bar: choose a round length that is 160–400 px on screen
          const lens = [1, 2, 5, 10, 20, 50, 100, 200, 500];
          const m = lens.find((L) => L * z >= 160) || 500;
          sbBar.style.width = m * z + "px";
          sbTxt.textContent = m + " m";
        },
      };
    },
  });
})();
