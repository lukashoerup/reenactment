"""Transcribe one episode window with word timings: python3 transcribe2.py MODEL WAV OFFSET_S"""
import sys, json
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[1], device="cpu", compute_type="int8", cpu_threads=2)
path, offset = sys.argv[2], float(sys.argv[3])
segs, info = m.transcribe(path, language="da", word_timestamps=True, beam_size=5, vad_filter=False)
out = []
for s in segs:
    out.append({"start": round(s.start+offset, 2), "end": round(s.end+offset, 2), "text": s.text.strip(),
                "words": [{"w": w.word, "s": round(w.start+offset, 2), "e": round(w.end+offset, 2)} for w in s.words]})
    mm, ss = divmod(s.start+offset, 60)
    print(f"{int(mm):02d}:{ss:05.2f}  {s.text.strip()}", flush=True)
json.dump(out, open(path.replace('.wav', '.json'), 'w'), ensure_ascii=False, indent=1)
print('done', flush=True)
