// quote — the speaker's own words, set in type, each word lighting up as it is spoken.
// Python aligns the corrected wording (p.text) to the transcript and passes p.words =
// [[word, seconds-after-shot-start], ...]. p.hl: phrases to set in ember.
(function () {
  const G = GFX;
  G.register("quote", {
    async setup(root, p) {
      const bg = G.el("div", "layer", root);
      bg.style.background = "radial-gradient(110% 100% at 20% 100%, #18272f 0%, #0f1b22 60%, #0b141a 100%)";
      const box = G.el("div", "", root);
      const words = p.words || [];
      const chars = words.reduce((n, w) => n + w[0].length + 1, 0);
      const size = p.size || (chars > 190 ? 58 : chars > 120 ? 68 : chars > 70 ? 80 : 96);
      Object.assign(box.style, { position: "absolute", left: "var(--safe-x)", right: "260px",
        top: "50%", transform: "translateY(-54%)" });
      const q = G.el("div", "t-quote", box);
      q.style.fontSize = size + "px";
      const hl = (p.hl || []).map((s) => s.toLowerCase().split(/\s+/));
      const lower = words.map((w) => w[0].toLowerCase().replace(/[^\wæøå]/g, ""));
      const hot = new Set();
      hl.forEach((ph) => {
        const n = ph.map((x) => x.replace(/[^\wæøå]/g, ""));
        for (let i = 0; i + n.length <= lower.length; i++)
          if (n.every((x, j) => lower[i + j] === x)) for (let j = 0; j < n.length; j++) hot.add(i + j);
      });
      const spans = words.map((w, i) => {
        const s = G.el("span", "", q, G.esc(w[0]) + " ");
        if (hot.has(i)) s.style.color = "var(--glod)";
        return s;
      });
      const att = p.who ? G.el("div", "", box,
        `<div class="t-stamp" style="font-size:44px;font-weight:600;margin-top:44px">${G.esc(p.who)}</div>` +
        (p.role ? `<div class="t-small" style="font-size:32px;margin-top:6px">${G.esc(p.role)}</div>` : "")) : null;
      const bar = G.el("div", "", box);
      Object.assign(bar.style, { position: "absolute", left: "-56px", top: "14px", width: "4px", bottom: att ? "120px" : "8px",
        background: "var(--glod)", transformOrigin: "50% 0%" });
      const lead = p.lead ?? 0.08; // light a word a hair before it is heard
      return {
        frame(t) {
          spans.forEach((s, i) => {
            const k = G.seg(t, words[i][1] - lead, words[i][1] - lead + 0.22);
            s.style.opacity = 0.17 + 0.83 * k;
          });
          const o = G.show(box, t, p.at ?? -0.2, p.until, 0.4, 0.4);
          bar.style.transform = `scaleY(${G.ease.out(G.seg(t, (p.at ?? -0.2), (p.at ?? -0.2) + 0.8))})`;
          if (att) G.show(att, t, p.who_at ?? 0.4, p.until, 0.6);
          return o;
        },
      };
    },
  });
})();
