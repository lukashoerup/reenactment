"""Cut section 2 (5:06.3–9:01.5 + a short tail): frame-exact on the episode clock, a few dissolves, and a sound
bed built in post (rain outside, the same rain muffled indoors, ducked under the narration). No generated audio.
python3 sec2/edit.py out/sec2_C_v1.mp4
Sources: sec2/clips/<id>.mp4 (stills with 12-frame handles, maps exact), Veo picks in sec2/picks.json (ambient shots,
6 s played at ~0.5x with every frame held twice or so, "on twos").
"""
import json, os, subprocess, sys
import numpy as np, cv2

OUT = sys.argv[1]; FPS, W, H, SR = 24, 1280, 720, 48000
D = json.load(open("sec2/shots.json")); shots = D["shots"]; TAIL = D["tail"]
picks = json.load(open("sec2/picks.json")) if os.path.exists("sec2/picks.json") else {}
F0 = round(shots[0]["start"] * FPS)
HANDLE = 12
DISSOLVE = {("t12", "t13"): 16, ("t13", "t14"): 12, ("t14", "t15"): 12, ("t19", "t20"): 12, ("t20", "t21"): 12}
RAIN = {"t03": .30, "t07": .30, "t16": .42, "t10": .26, "t17": .26}          # louder rain where the picture shows it
MAP_BED = .12

def frames_of(path):
    cap = cv2.VideoCapture(path); out = []
    while True:
        ok, f = cap.read()
        if not ok: break
        out.append(cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA) if f.shape[1] != W else f)
    return out

class Source:
    """Frame k of a shot (k may be negative / past the end for dissolves: handles if present, else held)."""
    def __init__(self, s):
        self.s = s; self.n = round(s["end"] * FPS) - round(s["start"] * FPS)
        if s["kind"] == "ambient":
            p = (picks.get(s["id"]) or {}).get("pick")
            if not p or not os.path.exists(p):   # no usable take: fall back to the still treatment
                p = f"sec2/clips/{s['id']}.mp4"; self.kind = "still"
            else: self.kind = "ambient"
        else: self.kind, p = s["kind"], f"sec2/clips/{s['id']}.mp4"
        if s is shots[-1]: self.n += round(TAIL * FPS)
        self.fr = frames_of(p); self.path = p
        self.off = HANDLE if self.kind == "still" and len(self.fr) >= self.n + HANDLE else 0
    def get(self, k):
        if self.kind == "ambient":
            r = len(self.fr) / self.n                    # source frames per output frame (≈ 0.5)
            i = int(np.floor(k * r))
        else: i = k + self.off
        return self.fr[min(max(i, 0), len(self.fr) - 1)]

def video():
    total = sum(round(s["end"] * FPS) - round(s["start"] * FPS) for s in shots) + round(TAIL * FPS)
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    label = (f"drawtext=fontfile={font}:text='REKONSTRUKTION  ·  TEGNET MED AI':fontsize=18:fontcolor=white@0.85:x=40:y=34:"
             f"alpha='if(lt(t,0.6),t/0.6,if(lt(t,6),1,if(lt(t,7),7-t,0)))':enable='lt(t,7)'")
    T = total / FPS
    vf = (f"format=yuv420p,noise=alls=4:allf=t,vignette=angle=PI/6,{label},fade=t=in:st=0:d=0.8,"
          f"fade=t=out:st={T - 1.6:.3f}:d=1.6")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                          "sec2/_video.mp4"], stdin=subprocess.PIPE)
    cache = {}
    def src_of(i):                                          # at most the previous, current and next shot in memory
        for k in [k for k in cache if k < i - 1]: del cache[k]
        if i not in cache:
            cache[i] = Source(shots[i]); print(shots[i]["id"], cache[i].kind, len(cache[i].fr), "frames for", cache[i].n, flush=True)
        return cache[i]
    for idx, s in enumerate(shots):
        src = src_of(idx); n = src.n
        din = DISSOLVE.get((shots[idx - 1]["id"], s["id"]), 0) if idx else 0
        dout = DISSOLVE.get((s["id"], shots[idx + 1]["id"]), 0) if idx + 1 < len(shots) else 0
        for k in range(n):
            f = src.get(k).astype(np.float32)
            if dout and k >= n - dout // 2:                 # second half of an outgoing dissolve: blend in the next shot
                j = k - n; w = (j + dout / 2 + .5) / dout
                f = f * (1 - w) + src_of(idx + 1).get(j).astype(np.float32) * w
            if din and k < din // 2:                         # first half of an incoming dissolve: blend with the last shot
                prev = cache[idx - 1]; j = prev.n + k; w = (k + din / 2 + .5) / din
                f = prev.get(j).astype(np.float32) * (1 - w) + f * w
            p.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    return total

def pcm(args):
    r = subprocess.run(["ffmpeg", "-v", "error"] + args + ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()

def loop(x, n, xf=3 * SR):
    out = np.zeros((n, 2), np.float32); pos = 0; ramp = np.linspace(0, 1, xf)[:, None]
    while pos < n:
        seg = x.copy(); seg[:xf] *= ramp if pos else 1; seg[-xf:] *= ramp[::-1]
        m = min(len(seg), n - pos); out[pos:pos + m] += seg[:m]; pos += len(seg) - xf
    return out

def smooth(g, sec):
    k = max(1, int(sec * SR)); c = np.cumsum(np.concatenate([[0], g]))
    return ((c[k:] - c[:-k]) / k)[np.clip(np.arange(len(g)) - k // 2, 0, len(g) - k)]

def audio(total):
    n = int(total / FPS * SR)
    t0 = shots[0]["start"]; t_end = shots[-1]["end"] + 0.1
    narr = pcm(["-ss", f"{t0:.3f}", "-t", f"{t_end - t0:.3f}", "-i", "audio/episode.mp3"])
    fo = int(0.25 * SR); narr[-fo:] *= np.linspace(1, 0, fo)[:, None]
    narr[:int(.08 * SR)] *= np.linspace(0, 1, int(.08 * SR))[:, None]
    narr = np.concatenate([narr, np.zeros((max(0, n - len(narr)), 2), np.float32)])[:n]
    rain = pcm(["-ss", "12", "-i", "sfx/1262.mp3", "-af", "highpass=f=90"])
    muff = pcm(["-ss", "12", "-i", "sfx/1262.mp3", "-af", "lowpass=f=450,lowpass=f=450,volume=2.2"])
    rain, muff = loop(rain, n), loop(muff, n)
    g_out, g_in = np.zeros(n, np.float32), np.zeros(n, np.float32)
    for s in shots:
        a = int((s["start"] - t0) * SR); b = int((s["end"] - t0) * SR) if s is not shots[-1] else n
        if s["audio"] == "int": g_in[a:b] = .55
        else: g_out[a:b] = MAP_BED if s["kind"] == "map" else RAIN.get(s["id"], .20)
    g_out, g_in = smooth(g_out, 2.0), smooth(g_in, 2.0)          # beds change over two seconds, never at the cut
    env = smooth(np.abs(narr).mean(1), .05)
    duck = 1 - .55 * np.clip(env / .04, 0, 1)
    duck = np.minimum(duck, smooth(duck, .6))           # fast down, slow up
    bed = (rain * g_out[:, None] + muff * g_in[:, None]) * duck[:, None]
    end = np.ones(n, np.float32); fl = int(1.6 * SR); end[-fl:] = np.linspace(1, 0, fl)
    mix = (narr + bed) * end[:, None]
    peak = np.abs(mix).max(); mix *= min(1.0, .93 / peak)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "sec2/_audio.wav"],
                   input=mix.astype(np.float32).tobytes(), check=True)

if __name__ == "__main__":
    total = video(); audio(total)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "sec2/_video.mp4", "-i", "sec2/_audio.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
    print("wrote", OUT, f"{total / FPS:.2f}s")
