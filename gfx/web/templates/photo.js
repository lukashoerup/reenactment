// photo — a real photograph (with its credit), moved by a slow camera and graded into the
// night palette. Never a generated image. p.src is relative to the episode folder.
(function () {
  const G = GFX;
  G.register("photo", {
    async setup(root, p, spec) {
      const wrap = G.el("div", "layer", root);
      wrap.style.overflow = "hidden";
      const img = G.el("img", "", wrap);
      img.src = spec.base + "/ep/" + p.src;
      await img.decode();
      const iw = img.naturalWidth, ih = img.naturalHeight;
      const cover = Math.max(1920 / iw, 1080 / ih);
      Object.assign(img.style, { position: "absolute", left: 0, top: 0, width: iw + "px", height: ih + "px", transformOrigin: "0 0" });
      if (p.grade !== "none") img.style.filter = p.filter || "saturate(.5) brightness(.78) contrast(1.06)";
      const tint = G.el("div", "layer", wrap);
      tint.style.background = p.grade === "none" ? "transparent" : "linear-gradient(180deg, rgba(15,27,34,.25), rgba(15,27,34,.55))";
      tint.style.mixBlendMode = "multiply";
      const shade = G.el("div", "layer", wrap);
      shade.style.background = "linear-gradient(0deg, rgba(10,18,23,.85) 0%, rgba(10,18,23,0) 45%)";
      shade.style.opacity = p.caption ? 1 : 0.4;
      let cap = null, capLines = null;
      if (p.caption) {
        cap = G.el("div", "cap", root);
        if (p.caption.k) G.el("div", "k", cap, G.esc(p.caption.k));
        const h = G.el("div", "h", cap);
        h.style.fontSize = (p.caption.size || 72) + "px";
        capLines = G.lines(h, [].concat(p.caption.h || []));
        if (p.caption.s) cap.sEl = G.el("div", "s", cap, G.esc(p.caption.s));
      }
      if (spec.credit) G.el("div", "credit", root, G.esc(spec.credit));
      const A = p.from || { x: 0.5, y: 0.5, s: 1.0 }, B = p.to || { x: 0.5, y: 0.5, s: 1.08 };
      return {
        frame(t) {
          const k = G.ease.inOutSine(G.seg(t, 0, spec.dur));
          const s = cover * G.lerp(A.s, B.s, k);
          const cx = G.lerp(A.x, B.x, k) * iw, cy = G.lerp(A.y, B.y, k) * ih;
          let tx = 960 - cx * s, ty = 540 - cy * s;
          tx = Math.min(0, Math.max(1920 - iw * s, tx));
          ty = Math.min(0, Math.max(1080 - ih * s, ty));
          img.style.transform = `translate(${tx}px,${ty}px) scale(${s})`;
          if (cap) {
            capLines(t, p.caption.at ?? 0.4);
            if (cap.sEl) G.show(cap.sEl, t, (p.caption.at ?? 0.4) + 0.6, p.caption.until);
            if (p.caption.until !== undefined) cap.style.opacity = 1 - G.seg(t, p.caption.until - 0.5, p.caption.until);
          }
        },
      };
    },
  });
})();
