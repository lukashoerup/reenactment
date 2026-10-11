// Frame-deterministic runtime. Python calls setupShot(spec) once per shot, then
// renderFrame(t) for every frame (t = seconds since the shot's first frame) and takes a
// screenshot. Nothing animates on its own: every visible state is a function of t.
(function () {
  const G = (window.GFX = { templates: {} });
  G.register = (name, impl) => (G.templates[name] = impl);

  // ---------- math ----------
  G.clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  G.lerp = (a, b, p) => a + (b - a) * p;
  G.seg = (t, a, b) => (b <= a ? (t >= a ? 1 : 0) : G.clamp((t - a) / (b - a)));
  G.ease = {
    linear: (p) => p,
    inOut: (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
    inOutSine: (p) => -(Math.cos(Math.PI * p) - 1) / 2,
    out: (p) => 1 - Math.pow(1 - p, 3),
    outExpo: (p) => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * p)),
    in: (p) => p * p * p,
  };
  // keyframes: [{at, v}] (numbers or arrays) -> value at t
  G.kf = (t, keys, ease = G.ease.inOut) => {
    if (!keys || !keys.length) return undefined;
    if (t <= keys[0].at) return keys[0].v;
    for (let i = 0; i < keys.length - 1; i++) {
      const a = keys[i], b = keys[i + 1];
      if (t <= b.at) {
        const p = (b.ease ? G.ease[b.ease] : ease)(G.seg(t, a.at, b.at));
        if (Array.isArray(a.v)) return a.v.map((x, j) => G.lerp(x, b.v[j], p));
        return G.lerp(a.v, b.v, p);
      }
    }
    return keys[keys.length - 1].v;
  };
  // deterministic pseudo-random
  G.rand = (i) => { const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); };

  // ---------- DOM ----------
  G.el = (tag, cls, parent, html) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    if (parent) parent.appendChild(e);
    return e;
  };
  G.esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  // Lines that wipe up from a mask. Returns a function (p in 0..1) -> applies state.
  G.lines = (parent, texts, cls) => {
    const spans = texts.map((txt) => {
      const l = G.el("span", "line " + (cls || ""), parent);
      return G.el("span", "", l, G.esc(txt));
    });
    return (t, at, stagger = 0.12, dur = 0.7) => {
      spans.forEach((s, i) => {
        const p = G.ease.out(G.seg(t, at + i * stagger, at + i * stagger + dur));
        s.style.transform = `translateY(${(1 - p) * 105}%)`;
        s.style.opacity = p > 0 ? 1 : 0;
      });
    };
  };
  // Fade an element in at `at` and out at `until` (both optional).
  G.show = (e, t, at, until, din = 0.5, dout = 0.4) => {
    let o = at === undefined ? 1 : G.ease.out(G.seg(t, at, at + din));
    if (until !== undefined) o *= 1 - G.seg(t, until - dout, until);
    e.style.opacity = o;
    return o;
  };

  // ---------- rain overlay (procedural, deterministic) ----------
  function makeRain(parent, amount) {
    const c = G.el("canvas", "layer", parent);
    c.width = 1920; c.height = 1080;
    c.style.zIndex = 40; c.style.mixBlendMode = "screen";
    const ctx = c.getContext("2d");
    const n = Math.round(900 * amount);
    return (t) => {
      ctx.clearRect(0, 0, 1920, 1080);
      ctx.lineCap = "round";
      for (let i = 0; i < n; i++) {
        const sp = 2200 + 1400 * G.rand(i * 3.1);        // px/s
        const len = 26 + 46 * G.rand(i * 7.7);
        const x0 = G.rand(i * 1.3) * 2200 - 140;
        const y = ((G.rand(i * 5.9) * 1300 + t * sp) % 1300) - 110;
        const x = x0 + y * 0.12;
        const a = 0.05 + 0.13 * G.rand(i * 2.2);
        ctx.strokeStyle = `rgba(200,215,225,${a})`;
        ctx.lineWidth = 1 + G.rand(i * 4.4) * 1.2;
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + len * 0.12, y + len); ctx.stroke();
      }
    };
  }

  // ---------- shot lifecycle ----------
  let current = null;
  window.setupShot = async (spec) => {
    const stage = document.getElementById("stage");
    stage.innerHTML = "";
    const impl = G.templates[spec.type];
    if (!impl) throw new Error("unknown template: " + spec.type);
    const root = G.el("div", "layer", stage);
    const fade = G.el("div", "fade", stage);
    const rain = spec.rain ? makeRain(stage, spec.rain === true ? 1 : spec.rain) : null;
    await document.fonts.ready;
    const ctl = await impl.setup(root, spec.p || {}, spec);
    // lower third: who is speaking (any template can carry one)
    let lt = null;
    if (spec.lt) {
      lt = G.el("div", "", stage);
      Object.assign(lt.style, { position: "absolute", left: "var(--safe-x)", top: spec.lt.top ? "var(--safe-y)" : "auto",
        bottom: spec.lt.top ? "auto" : "var(--safe-y)", zIndex: 45, paddingLeft: "26px", borderLeft: "4px solid var(--glod)" });
      lt.innerHTML = `<div class="t-stamp" style="font-size:46px;font-weight:620;text-shadow:0 2px 16px rgba(8,14,18,.9)">${G.esc(spec.lt.name)}</div>` +
        `<div class="t-small" style="font-size:30px;margin-top:4px;color:#b4bec2;text-shadow:0 2px 14px rgba(8,14,18,.95)">${G.esc(spec.lt.role || "")}</div>`;
    }
    current = { spec, ctl, fade, rain, lt };
    return true;
  };
  window.renderFrame = async (t) => {
    const { spec, ctl, fade, rain, lt } = current;
    if (lt) {
      const a = spec.lt.at ?? 0.3, u = spec.lt.until ?? a + 5;
      const k = G.ease.out(G.seg(t, a, a + 0.6)) * (1 - G.seg(t, u - 0.5, u));
      lt.style.opacity = k;
      lt.style.transform = `translateX(${(1 - G.ease.out(G.seg(t, a, a + 0.6))) * -30}px)`;
    }
    const d = spec.dur;
    let f = 0;
    if (spec.fade_in) f = Math.max(f, 1 - G.seg(t, spec.t0 || 0, (spec.t0 || 0) + spec.fade_in));
    if (spec.fade_out) f = Math.max(f, G.seg(t, d - spec.fade_out, d));
    fade.style.opacity = f;
    if (rain) rain(t);
    if (ctl.frame) await ctl.frame(t);
    return true;
  };
})();
