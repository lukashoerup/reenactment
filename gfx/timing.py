"""Episode clock: parse timecodes and resolve word anchors against the transcript.

A time in a scene file is one of
  "03:41.5"                         episode time (mm:ss or h:mm:ss)
  {"word": "Køge", "near": "03:18"} start of the spoken word nearest to `near`
  {"word": "regnvejrstunge september", "near": "04:06", "edge": "end", "offset": 0.2}
  2.5                               (only inside a shot) seconds after the shot starts
Words are matched loosely (case, punctuation and Whisper's spelling slips are tolerated),
so the scene file can be written in correct Danish while the transcript has errors.
"""
import difflib, json, os, re, unicodedata

TIME_RE = re.compile(r"^(\d+:)?\d{1,2}:\d{1,2}(\.\d+)?$")


def parse_tc(s):
    p = [float(x) for x in str(s).split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


def fmt_tc(x):
    m, s = divmod(max(0.0, x), 60)
    return f"{int(m):02d}:{s:05.2f}"


def norm(w):
    w = unicodedata.normalize("NFC", w.lower())
    return re.sub(r"[^\wæøå]", "", w)


class Transcript:
    def __init__(self, path):
        self.path = path
        self.segs = json.load(open(path)) if os.path.exists(path) else []
        self.words = [dict(w, n=norm(w["w"])) for s in self.segs for w in s["words"] if norm(w["w"])]

    def text_between(self, a, b):
        return " ".join(w["w"] for w in self.words if a <= w["s"] < b)

    def find(self, phrase, near, window=12.0):
        """Best match for `phrase` (one or more words) near episode time `near`."""
        target = [norm(x) for x in phrase.split() if norm(x)]
        if not target:
            raise ValueError("empty anchor")
        cands = [i for i, w in enumerate(self.words) if abs(w["s"] - near) <= window]
        best, best_score = None, 0.0
        for i in cands:
            seq = self.words[i:i + len(target)]
            if len(seq) < len(target):
                continue
            sc = sum(difflib.SequenceMatcher(None, a, b["n"]).ratio() for a, b in zip(target, seq)) / len(target)
            sc -= abs(seq[0]["s"] - near) / (window * 20)  # tie-break on distance
            if sc > best_score:
                best, best_score = (seq[0], seq[-1]), sc
        if not best or best_score < 0.6:
            raise ValueError(f"anchor '{phrase}' not found near {fmt_tc(near)} (best score {best_score:.2f})")
        return best

    def resolve(self, v):
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            return parse_tc(v)
        if isinstance(v, dict) and "word" in v:
            first, last = self.find(v["word"], parse_tc(v["near"]), v.get("window", 12.0))
            t = last["e"] if v.get("edge") == "end" else first["s"]
            return t + float(v.get("offset", 0.0))
        raise ValueError(f"cannot resolve time {v!r}")

    def words_between(self, a, b):
        return [w for w in self.words if a - 0.05 <= w["s"] < b]

    def align(self, text, a, b):
        """Give every word of `text` (the corrected wording) a time from the spoken words in [a, b)."""
        spoken = self.words_between(a, b)
        mine = text.split()
        sm = difflib.SequenceMatcher(None, [norm(x) for x in mine], [w["n"] for w in spoken], autojunk=False)
        times = [None] * len(mine)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                times[blk.a + k] = spoken[blk.b + k]["s"]
        # fill gaps by interpolating between known neighbours
        known = [(i, t) for i, t in enumerate(times) if t is not None]
        if not known:
            step = (b - a) / max(1, len(mine))
            return [(m, a + i * step) for i, m in enumerate(mine)]
        for i in range(len(mine)):
            if times[i] is None:
                prev = max([k for k in known if k[0] < i], default=(None, a), key=lambda k: k[0] if k[0] is not None else -1)
                nxt = min([k for k in known if k[0] > i], default=(len(mine), b), key=lambda k: k[0])
                pi, pt = (prev[0] if prev[0] is not None else -1), prev[1]
                times[i] = pt + (nxt[1] - pt) * (i - pi) / max(1, nxt[0] - pi)
        return list(zip(mine, times))
