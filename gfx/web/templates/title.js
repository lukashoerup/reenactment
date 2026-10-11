// title — time/place stamps and big statements over a night background.
// card  — chapter cards (a numbered sequence, so the number carries meaning).
(function () {
  const G = GFX;
  function night(root, p) {
    const bg = G.el("div", "layer", root);
    bg.style.background = p.bg === "black" ? "#000"
      : "radial-gradient(120% 90% at 30% 110%, #1b2c34 0%, #0f1b22 55%, #0a1217 100%)";
    const mist = G.el("div", "layer", root);
    mist.style.background = "radial-gradient(60% 40% at 50% 60%, rgba(143,156,162,.07), rgba(0,0,0,0) 70%)";
    return (t) => { mist.style.transform = `translate(${Math.sin(t * 0.13) * 40}px, ${Math.cos(t * 0.11) * 18}px) scale(1.15)`; };
  }

  G.register("title", {
    async setup(root, p) {
      const drift = night(root, p);
      const box = G.el("div", "", root);
      const pos = p.pos || "lower-left";
      Object.assign(box.style, { position: "absolute", left: "var(--safe-x)", maxWidth: "1500px",
        ...(pos === "lower-left" ? { bottom: "150px" } : { top: "50%", transform: "translateY(-50%)" }) });
      const k = p.kicker ? G.el("div", "t-small", box, G.esc(p.kicker)) : null;
      if (k) Object.assign(k.style, { fontSize: "34px", marginBottom: "18px" });
      const big = G.el("div", "t-stamp", box);
      big.style.fontSize = (p.size || 200) + "px";
      if (p.hot) big.style.color = "var(--glod)";
      const reveal = G.lines(big, [].concat(p.lines || []));
      const sub = p.sub ? G.el("div", "t-body", box, G.esc(p.sub)) : null;
      if (sub) Object.assign(sub.style, { marginTop: "26px", color: "#c9c6bd", maxWidth: "1150px", fontSize: "44px" });
      const at = p.at ?? 0.2;
      return {
        frame(t) {
          drift(t);
          if (k) G.show(k, t, at, p.until, 0.6);
          reveal(t, at + 0.15, 0.14, 0.8);
          if (sub) G.show(sub, t, p.sub_at ?? at + 0.8, p.until, 0.7);
          if (p.until !== undefined) box.style.opacity = 1 - G.seg(t, p.until - 0.5, p.until);
          // a very slow push keeps a held title alive without inventing motion
          const z = 1 + 0.025 * G.seg(t, 0, 12);
          big.style.transform = `scale(${z})`; big.style.transformOrigin = "0% 100%";
        },
      };
    },
  });

  G.register("card", {
    async setup(root, p) {
      const drift = night(root, { bg: p.bg || "black" });
      const box = G.el("div", "", root);
      Object.assign(box.style, { position: "absolute", left: "var(--safe-x)", top: "50%", transform: "translateY(-50%)" });
      const num = p.num ? G.el("div", "t-stamp", box, G.esc(p.num)) : null;
      if (num) Object.assign(num.style, { fontSize: "56px", color: "var(--glod)", marginBottom: "18px", fontStretch: "100%" });
      const ttl = G.el("div", "t-display", box);
      ttl.style.fontSize = "128px";
      const rev = G.lines(ttl, [].concat(p.title));
      const sub = p.sub ? G.el("div", "t-small", box, G.esc(p.sub)) : null;
      if (sub) Object.assign(sub.style, { fontSize: "36px", marginTop: "24px" });
      const at = p.at ?? 0.3;
      return {
        frame(t) {
          drift(t);
          if (num) G.show(num, t, at, p.until, 0.5);
          rev(t, at + 0.2, 0.1, 0.9);
          if (sub) G.show(sub, t, at + 0.9, p.until, 0.6);
          if (p.until !== undefined) box.style.opacity = 1 - G.seg(t, p.until - 0.5, p.until);
        },
      };
    },
  });
})();
