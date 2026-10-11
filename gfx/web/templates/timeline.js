// timeline — dated events on one axis; the view travels with the story.
(function () {
  const G = GFX;
  G.register("timeline", {
    async setup(root, p) {
      const bg = G.el("div", "layer", root);
      bg.style.background = "linear-gradient(180deg, #0f1b22 0%, #0c161c 100%)";
      const ev = p.events || [];
      const gap = p.gap || 560;
      const track = G.el("div", "", root);
      Object.assign(track.style, { position: "absolute", left: 0, top: "540px", height: "0", width: (ev.length * gap + 2000) + "px" });
      const axis = G.el("div", "", track);
      Object.assign(axis.style, { position: "absolute", left: "-400px", top: "-1px", height: "2px", width: (ev.length * gap + 1200) + "px",
        background: "var(--vej-2)", transformOrigin: "0 50%" });
      const items = ev.map((e, i) => {
        const x = 300 + i * gap;
        const dot = G.el("div", "", track);
        Object.assign(dot.style, { position: "absolute", left: x - 9 + "px", top: "-9px", width: "18px", height: "18px", borderRadius: "50%",
          background: e.hot ? "var(--glod)" : "var(--papir)", boxShadow: "0 0 0 6px #0f1b22" });
        const top = G.el("div", "t-stamp", track, G.esc(e.when));
        Object.assign(top.style, { position: "absolute", left: x - 9 + "px", bottom: "40px", fontSize: "64px", whiteSpace: "nowrap",
          color: e.hot ? "var(--glod)" : "var(--papir)" });
        const below = G.el("div", "", track, `<div class="t-body" style="font-size:42px;line-height:1.15">${G.esc(e.label || "")}</div>` +
          (e.sub ? `<div class="t-small" style="margin-top:10px">${G.esc(e.sub)}</div>` : ""));
        Object.assign(below.style, { position: "absolute", left: x - 9 + "px", top: "44px", width: gap - 90 + "px" });
        return { e, x, dot, top, below };
      });
      const focusX = (t) => {
        let k = 0;
        items.forEach((it, i) => { if (t >= (it.e.at ?? 0)) k = i; });
        return k;
      };
      return {
        frame(t) {
          axis.style.transform = `scaleX(${G.ease.out(G.seg(t, p.at ?? 0, (p.at ?? 0) + 1.2))})`;
          // camera: ease from the previous focus to the current one
          let off = 0;
          for (let i = 1; i < items.length; i++) {
            const at = items[i].e.at ?? 0;
            const move = G.ease.inOut(G.seg(t, at - 0.6, at + 0.4));
            const target = Math.max(0, items[i].x - (p.focus ?? 0.38) * 1920 + 300);
            const prev = Math.max(0, items[i - 1].x - (p.focus ?? 0.38) * 1920 + 300);
            if (t >= at - 0.6) off = G.lerp(prev, target, move);
          }
          track.style.transform = `translateX(${-off + (p.drift ? -t * p.drift : 0)}px)`;
          const f = focusX(t);
          items.forEach((it, i) => {
            const at = it.e.at ?? 0;
            const k = G.ease.out(G.seg(t, at, at + 0.6));
            const dim = i < f ? 0.45 : 1;
            it.dot.style.transform = `scale(${k})`;
            it.top.style.opacity = k * dim;
            it.below.style.opacity = G.ease.out(G.seg(t, at + 0.25, at + 0.85)) * dim;
            it.top.style.transform = `translateY(${(1 - k) * 18}px)`;
          });
          if (p.until !== undefined) track.style.opacity = 1 - G.seg(t, p.until - 0.5, p.until);
        },
      };
    },
  });
})();
