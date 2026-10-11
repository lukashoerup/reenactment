// facts — findings and reasoning, in two layouts:
//   list:  a heading and findings that arrive as they are named
//   chain: finding → meaning → conclusion, read left to right (the last link in ember)
(function () {
  const G = GFX;
  G.register("facts", {
    async setup(root, p) {
      const bg = G.el("div", "layer", root);
      bg.style.background = "linear-gradient(180deg, #101d24 0%, #0d171d 100%)";
      // faint measuring grid: the language of the lab / the case file, not a fake document
      const grid = G.el("div", "layer", root);
      grid.style.backgroundImage =
        "linear-gradient(rgba(143,156,162,.06) 1px, transparent 1px), linear-gradient(90deg, rgba(143,156,162,.06) 1px, transparent 1px)";
      grid.style.backgroundSize = "60px 60px";
      const box = G.el("div", "", root);
      Object.assign(box.style, { position: "absolute", left: "var(--safe-x)", right: "var(--safe-x)", top: "var(--safe-y)", bottom: "var(--safe-y)" });
      let head = null, headRev = null;
      if (p.heading) {
        head = G.el("div", "t-stamp", box);
        head.style.fontSize = "84px";
        headRev = G.lines(head, [].concat(p.heading));
      }
      const kick = p.kicker ? G.el("div", "t-small", box, G.esc(p.kicker)) : null;
      if (kick) Object.assign(kick.style, { fontSize: "32px", marginTop: "14px" });
      const items = p.items || [];
      const els = [];
      if ((p.layout || "list") === "list") {
        // findings arrive one by one; the newest is in focus, earlier ones step back
        box.style.top = "auto"; box.style.bottom = "auto";
        Object.assign(box.style, { top: "50%", transform: "translateY(-50%)" });
        const list = G.el("div", "", box);
        Object.assign(list.style, { marginTop: "56px", display: "flex", flexDirection: "column", gap: "26px", maxWidth: "1500px" });
        items.forEach((it) => {
          const row = G.el("div", "", list);
          const txt = G.el("div", "", row, `<div class="t-body" style="font-size:${it.size || 64}px;line-height:1.1;font-weight:460;letter-spacing:-.01em${it.hot ? ";color:var(--glod)" : ""}">${G.esc(it.text)}</div>` +
            (it.sub ? `<div class="t-small" style="font-size:32px;margin-top:8px">${G.esc(it.sub)}</div>` : ""));
          els.push({ it, row, txt });
        });
      } else {
        const chain = G.el("div", "", box);
        Object.assign(chain.style, { position: "absolute", left: 0, right: 0, top: "46%", transform: "translateY(-50%)",
          display: "flex", alignItems: "flex-start", gap: "0" });
        items.forEach((it, i) => {
          if (i > 0) {
            const arrow = G.el("div", "", chain);
            Object.assign(arrow.style, { flex: "0 0 64px", height: "2px", background: "var(--taage)", marginTop: "52px",
              marginLeft: "18px", marginRight: "18px", position: "relative", transformOrigin: "0 50%" });
            G.el("div", "", arrow).style.cssText = "position:absolute;right:-2px;top:-7px;width:16px;height:16px;border-top:2px solid var(--taage);border-right:2px solid var(--taage);transform:rotate(45deg)";
            els.push({ arrow, it });
          }
          const last = i === items.length - 1;
          const node = G.el("div", "", chain, `<div class="t-body" style="font-size:${it.size || 50}px;font-stretch:84%;line-height:1.12;font-weight:${last ? 600 : 480}${last || it.hot ? ";color:var(--glod)" : ""}">${G.esc(it.text)}</div>` +
            (it.sub ? `<div class="t-small" style="font-size:30px;margin-top:14px">${G.esc(it.sub)}</div>` : ""));
          Object.assign(node.style, { flex: "1 1 0", minWidth: 0, borderTop: `4px solid ${last || it.hot ? "var(--glod)" : "var(--papir)"}`, paddingTop: "22px" });
          els.push({ node, it });
        });
      }
      return {
        frame(t) {
          if (headRev) headRev(t, p.at ?? 0.1, 0.1, 0.7);
          if (kick) G.show(kick, t, (p.at ?? 0.1) + 0.5, p.until);
          els.forEach((e) => {
            const at = e.it.at ?? 0.6;
            if (e.row) {
              const k = G.ease.out(G.seg(t, at, at + 0.6));
              const later = els.filter((o) => o.row && (o.it.at ?? 0.6) > at).map((o) => o.it.at ?? 0.6);
              const next = later.length ? Math.min(...later) : Infinity;
              const back = p.focus === false ? 0 : G.seg(t, next - 0.1, next + 0.5);
              e.row.style.opacity = k * (1 - 0.55 * back);
              e.txt.style.transform = `translateY(${(1 - k) * 22}px)`;
            } else if (e.arrow) {
              const k = G.ease.out(G.seg(t, at - 0.5, at));
              e.arrow.style.transform = `scaleX(${k})`;
              e.arrow.style.opacity = k > 0 ? 1 : 0;
            } else {
              const k = G.ease.out(G.seg(t, at, at + 0.7));
              e.node.style.opacity = k;
              e.node.style.transform = `translateY(${(1 - k) * 20}px)`;
            }
          });
          if (p.until !== undefined) box.style.opacity = 1 - G.seg(t, p.until - 0.5, p.until);
        },
      };
    },
  });
})();
