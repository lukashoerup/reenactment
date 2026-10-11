"""Transcribe the episode (or windows of it) with word timings.

    python3 transcribe.py --all                   # whole episode, 5-min chunks, resumable
    python3 transcribe.py --merge                 # only rebuild audio/transcript.json
    python3 transcribe.py 03:15-06:15 09:20-13:15 # only these windows
    python3 transcribe.py --model small ...       # faster, less accurate

Writes one JSON per chunk to audio/tx/ (skips chunks already done) and merges all of
them into audio/transcript.json: [{start, end, text, words:[{w,s,e}]}] on the episode
clock. Media stays out of git (audio/ is ignored).
"""
import json, os, subprocess, sys, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "audio", "episode.mp3")
TX = os.path.join(ROOT, "audio", "tx")


def secs(s):
    p = [float(x) for x in s.split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


def duration():
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", SRC]).decode().strip()
    return float(out)


def merge():
    segs = []
    for f in sorted(glob.glob(os.path.join(TX, "*.json"))):
        segs += json.load(open(f))
    segs.sort(key=lambda s: s["start"])
    out, last_end = [], -1
    for s in segs:  # chunks overlap by a few seconds: keep the first copy
        if s["start"] < last_end - 0.5:
            continue
        out.append(s)
        last_end = s["end"]
    json.dump(out, open(os.path.join(ROOT, "audio", "transcript.json"), "w"), ensure_ascii=False, indent=1)
    return out


def main():
    args = sys.argv[1:]
    model = "medium"
    if "--model" in args:
        i = args.index("--model")
        model = args[i + 1]
        del args[i:i + 2]
    if args == ["--merge"]:
        merge()
        return
    if args and args != ["--all"]:
        wins = [tuple(secs(x) for x in a.split("-")) for a in args]
    elif args == ["--all"]:
        d, step = duration(), 300.0
        wins = [(t, min(d, t + step + 3)) for t in [i * step for i in range(int(d // step) + 1)] if t < d]
    else:
        raise SystemExit(__doc__)
    os.makedirs(TX, exist_ok=True)
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 2)
    for a, b in wins:
        out_json = os.path.join(TX, f"{int(a):05d}_{int(b):05d}.json")
        if os.path.exists(out_json):
            continue
        # decode with ffmpeg ourselves (PyAV versions differ in what faster-whisper expects)
        import numpy as np
        raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", str(a), "-to", str(b), "-i", SRC,
                                       "-ac", "1", "-ar", "16000", "-f", "f32le", "-"])
        pcm = np.frombuffer(raw, dtype=np.float32)
        segs, _ = m.transcribe(pcm, language="da", word_timestamps=True, beam_size=5,
                               vad_filter=True, condition_on_previous_text=False)
        out = []
        for s in segs:
            out.append({"start": round(s.start + a, 2), "end": round(s.end + a, 2), "text": s.text.strip(),
                        "words": [{"w": w.word.strip(), "s": round(w.start + a, 2), "e": round(w.end + a, 2)}
                                  for w in s.words]})
            mm, ss = divmod(s.start + a, 60)
            print(f"{int(mm):02d}:{ss:05.2f}  {s.text.strip()}", flush=True)
        json.dump(out, open(out_json, "w"), ensure_ascii=False, indent=1)
        print(f"---- {a:.0f}-{b:.0f} done", flush=True)
    merge()


if __name__ == "__main__":
    main()
