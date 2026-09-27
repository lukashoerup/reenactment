"""Automatic checks on a cut: frame-to-frame jumps inside shots, exposure/colour mismatch
across cuts, face detection (rule: no faces), and sound level jumps at the cuts."""
import sys, json, subprocess, numpy as np, cv2
path = sys.argv[1]; offs = float(sys.argv[2]) if len(sys.argv) > 2 else 0
sl = json.load(open("shotlist.json"))
cuts = [round(s["start"]*24) for s in sl["shots"]] + [round(sl["shots"][-1]["end"]*24)]
cap = cv2.VideoCapture(path)
frames = []
while True:
    ok, f = cap.read()
    if not ok: break
    frames.append(cv2.resize(f, (320, 180), interpolation=cv2.INTER_AREA))
n = len(frames)
gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in frames]
diff = np.array([0] + [np.abs(gray[i] - gray[i-1]).mean() for i in range(1, n)])
def shot_of(i):
    for k in range(len(cuts)-1):
        if cuts[k] <= i < cuts[k+1]: return sl["shots"][k]["id"]
    return "end"
print("== jumps inside shots (frame diff > 3x shot median) ==")
for k in range(len(cuts)-1):
    a, b = cuts[k]+1, min(cuts[k+1], n)
    if b - a < 4: continue
    d = diff[a:b]; med = np.median(d)
    spikes = [(a+i, round(float(v), 1)) for i, v in enumerate(d) if v > max(3*med, med+4)]
    print(sl["shots"][k]["id"], "median", round(float(med), 2), "spikes", spikes[:6])
print("== look per shot: mean luma, warm/cool balance (R-B) ==")
for k in range(len(cuts)-1):
    a, b = cuts[k], min(cuts[k+1], n)
    fs = np.stack(frames[a:b]).astype(np.float32)
    print(sl["shots"][k]["id"], "luma", round(float(fs.mean()), 1), "R-B", round(float((fs[..., 2]-fs[..., 0]).mean()), 1),
          "flicker(std of luma)", round(float(np.std([g.mean() for g in gray[a:b]])), 2))
print("== faces (Haar, frontal + profile), every 3rd frame, full res ==")
cap = cv2.VideoCapture(path); fc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
pc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
i = 0; hits = {}
while True:
    ok, f = cap.read()
    if not ok: break
    if i % 3 == 0:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        for c, name in ((fc, "front"), (pc, "profile")):
            r = c.detectMultiScale(g, 1.1, 6, minSize=(40, 40))
            if len(r): hits.setdefault(shot_of(i), []).append((round(i/24, 2), name, [list(map(int, x)) for x in r][:2]))
    i += 1
for s, h in hits.items(): print(s, len(h), "hits, first:", h[:3])
if not hits: print("none")
print("== sound: loudness around each cut (dB RMS, 0.25 s before/after) ==")
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
def db(a, b):
    seg = x[int(a*8000):int(b*8000)]; return round(float(20*np.log10(np.sqrt((seg**2).mean()) + 1e-9)), 1)
for k, c in enumerate(cuts[1:-1], 1):
    t = c/24; print(sl["shots"][k]["id"], f"{t:.2f}s", db(t-0.25, t), "->", db(t, t+0.25))
