import sys, json
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[1], device="cpu", compute_type="int8", cpu_threads=2)
for path, offset in [("audio/seg_0320_0620.wav",200),("audio/seg_2000_2120.wav",1200)]:
    segs, info = m.transcribe(path, language="da", word_timestamps=True, beam_size=5, vad_filter=False)
    out=[]
    for s in segs:
        out.append({"start":round(s.start+offset,2),"end":round(s.end+offset,2),"text":s.text.strip(),
                    "words":[{"w":w.word,"s":round(w.start+offset,2),"e":round(w.end+offset,2)} for w in s.words]})
        mm,ss=divmod(s.start+offset,60)
        print(f"{int(mm):02d}:{ss:05.2f}  {s.text.strip()}", flush=True)
    json.dump(out, open(path.replace('.wav','.json'),'w'), ensure_ascii=False, indent=1)
    print('----', flush=True)
