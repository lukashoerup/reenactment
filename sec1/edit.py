"""Cut section 1 (0:00–5:06.3) from picked takes + reused drawn clips, frame-accurate on the narration.
Step 1: normalise every shot to sec1/norm/<id>.mp4 (1280x720, 24 fps, exact frames, ambience audio).
Step 2: concat, light drawn-look finish, reconstruction label, narration + ducked ambience -> OUT.
python3 sec1/edit.py OUT.mp4 [--only-norm]
Missing picks fall back to the keyframe as a still with a slow push (method B), so a cut always exists.
"""
import json, os, subprocess, sys

OUT = sys.argv[1]; FPS = 24; W, H = 1280, 720
data = json.load(open("sec1/shots.json")); shots = data["shots"]
picks = json.load(open("sec1/picks.json")) if os.path.exists("sec1/picks.json") else {}
os.makedirs("sec1/norm", exist_ok=True)

def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                capture_output=True, text=True).stdout or 0)

def has_audio(f):
    return "audio" in subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", f],
                                     capture_output=True, text=True).stdout

def source(s):
    if s["kind"] == "reuse":
        if s["reuse"].startswith("CLIP:"):
            ref = s["reuse"][5:]; return (picks.get(ref) or {}).get("pick"), s["rin"]
        return s["reuse"], s["rin"]
    if s["image"] == "BLACK": return None, 0
    p = (picks.get(s["id"]) or {}).get("pick")
    if p and os.path.exists(p): return p, 0.0
    alt = sorted(f"sec1/clips/{f}" for f in os.listdir("sec1/clips") if f.startswith(s["id"] + "_t") and "_use" not in f) if os.path.isdir("sec1/clips") else []
    return (alt[0], 0.0) if alt else ("KF", 0.0)

MONO_POST = {"s30"}   # video model added a red smear on the newspaper; this shot is grey paper anyway
frames = []
for s in shots:
    a, b = round(s["start"] * FPS), round(s["end"] * FPS)
    frames.append(b - a)
    n = b - a; out = f"sec1/norm/{s['id']}.mp4"; T = n / FPS
    src, rin = source(s)
    marker = f"sec1/norm/{s['id']}.src"; key = f"{src}|{rin}|{n}|{'mono' if s['id'] in MONO_POST else ''}"
    if os.path.exists(out) and os.path.exists(marker) and open(marker).read() == key:
        continue
    base = ["ffmpeg", "-v", "error", "-y"]
    if src is None:   # black
        cmd = base + ["-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={T:.4f}", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
                      "-t", f"{T:.4f}", "-frames:v", str(n), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out]
    elif src == "KF":  # still fallback with a slow push
        cmd = base + ["-loop", "1", "-i", f"sec1/kf/{s['id']}.png", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                      "-vf", f"scale={W*2}:{H*2},zoompan=z='1+0.06*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},setsar=1",
                      "-frames:v", str(n), "-t", f"{T:.4f}", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", out]
    else:
        avail = dur(src) - rin
        speed = min(1.0, avail / T) if avail > 0 else 1.0     # slow down (<1) only when the clip is too short
        pts = f"setpts=(PTS-STARTPTS)/{speed:.5f}" if speed < 0.999 else "setpts=PTS-STARTPTS"
        post = ",hue=s=0" if s["id"] in MONO_POST else ""
        vf = f"[0:v]trim=start={rin},{pts},fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1{post},tpad=stop_mode=clone:stop_duration=2,trim=end_frame={n}[v]"
        if has_audio(src):
            af = (f"[0:a]atrim=start={rin},asetpts=PTS-STARTPTS,atempo={max(speed,0.5):.5f},aresample=48000,aformat=channel_layouts=stereo,"
                  f"apad,atrim=duration={T:.4f},afade=t=in:d=0.05,afade=t=out:st={max(T-0.05,0):.4f}:d=0.05[a]")
            cmd = base + ["-i", src, "-filter_complex", vf + ";" + af, "-map", "[v]", "-map", "[a]"]
        else:
            cmd = base + ["-i", src, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex", vf, "-map", "[v]", "-map", "1:a", "-t", f"{T:.4f}"]
        cmd += ["-frames:v", str(n), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", out]
        if speed < 0.999: print(f"{s['id']}: slowed to {speed:.2f}x (clip {avail:.2f}s, slot {T:.2f}s)")
    subprocess.run(cmd, check=True)
    open(marker, "w").write(key)
print("normalised", len(shots), "shots,", sum(frames), "frames =", sum(frames) / FPS, "s")
if "--only-norm" in sys.argv: sys.exit()

open("sec1/norm/list.txt", "w").write("".join(f"file '{s['id']}.mp4'\n" for s in shots))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "sec1/norm/list.txt", "-c", "copy", "sec1/norm/_all.mp4"], check=True)
total = sum(frames) / FPS
font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
label = (f"drawtext=fontfile={font}:text='REKONSTRUKTION  ·  TEGNET MED AI':fontsize=18:fontcolor=white@0.85:x=40:y=34:"
         f"alpha='if(lt(t,0.6),t/0.6,if(lt(t,6),1,if(lt(t,7),7-t,0)))':enable='lt(t,7)'")
fc = ("[0:v]format=yuv420p,noise=alls=4:allf=t,vignette=angle=PI/6," + label +
      f",fade=t=in:st=0:d=0.8,fade=t=out:st={total-1.0:.3f}:d=1.0[v];"
      "[0:a]highpass=f=80,volume=0.28[amb];"
      f"[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={total:.3f},afade=t=out:st={total-1.2:.3f}:d=1.2,asplit[n1][n2];"
      "[amb][n2]sidechaincompress=threshold=0.03:ratio=5:attack=15:release=400[ambd];"
      "[n1][ambd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "sec1/norm/_all.mp4", "-ss", "0", "-t", f"{total:.3f}", "-i", "audio/episode.mp3",
                "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT], check=True)
print("wrote", OUT, f"{total:.2f}s")
