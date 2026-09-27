"""Cut the re-enactment: trims Veo clips to the shot list, grades them as one piece of film,
lays the episode narration on top with the clips' own rain/fire sound ducked underneath.
python3 edit.py OUT.mp4 [--version v1] [--nograde]
"""
import json, subprocess, sys, argparse

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--version", default="v1")
ap.add_argument("--nograde", action="store_true")
ap.add_argument("--light", action="store_true", help="drawn style: grain and vignette only")
ap.add_argument("--inmap", default="", help="JSON overrides for in-points")
ap.add_argument("--w", type=int, default=1920); ap.add_argument("--h", type=int, default=1080)
a = ap.parse_args()

sl = json.load(open("shotlist.json"))
CLIP_IN, CLIP_OUT = sl["clip_in"], sl["clip_out"]
# in-point inside each generated clip (seconds), chosen by reviewing the frames
IN = {"S1": 0.6, "S2": 1.6, "S3": 1.2, "S4": 0.7, "S5": 1.5, "S6": 1.4, "S7": 1.8, "S8": 2.2}
# per-shot exposure/saturation trims so the shots sit together
TRIM = {"S1": (0.00, 1.00), "S2": (-0.03, 0.92), "S3": (-0.02, 0.95), "S4": (-0.03, 0.92),
        "S5": (-0.06, 0.88), "S6": (-0.05, 0.88), "S7": (0.00, 1.00), "S8": (-0.04, 0.90)}
if a.inmap: IN.update(json.loads(a.inmap))
if a.light: TRIM = {k: (0.0, 1.0) for k in TRIM}
W, H = a.w, a.h
shots = [s for s in sl["shots"] if s["id"] != "S9"]
black = [s for s in sl["shots"] if s["id"] == "S9"][0]

inputs, vparts, aparts = [], [], []
for i, s in enumerate(shots):
    dur = round(s["end"] - s["start"], 3)
    inputs += ["-i", f"clips/{s['id']}_{a.version}.mp4"]
    b, sat = TRIM[s["id"]]
    t0 = IN[s["id"]]
    vparts.append(f"[{i}:v]trim=start={t0}:duration={dur},setpts=PTS-STARTPTS,fps=24,"
                  f"scale={W}:{H}:flags=lanczos,eq=brightness={b}:saturation={sat},setsar=1[v{i}]")
    aparts.append(f"[{i}:a]atrim=start={t0}:duration={dur},asetpts=PTS-STARTPTS,aresample=48000,"
                  f"aformat=channel_layouts=stereo[a{i}]")
n = len(shots)
bdur = round(black["end"] - black["start"], 3)
# black tail + rain for the black: reuse the rain from S1's first second, faded
vparts.append(f"color=c=black:s={W}x{H}:r=24:d={bdur},setsar=1[vb]")
aparts.append(f"[0:a]atrim=start=0:duration={bdur},asetpts=PTS-STARTPTS,aresample=48000,"
              f"aformat=channel_layouts=stereo,afade=t=out:st=0.2:d={bdur-0.2}[ab]")
# narration straight from the episode
inputs += ["-ss", str(CLIP_IN), "-t", str(round(CLIP_OUT - CLIP_IN, 3)), "-i", "audio/episode.mp3"]
nar = n

vcat = "".join(f"[v{i}]" for i in range(n)) + "[vb]"
acat = "".join(f"[a{i}]" for i in range(n)) + "[ab]"
grade = ("[vcat]format=gbrp,split[base][hl];"
         # halation: glow from the brightest parts only, pushed red like film
         f"[hl]scale={W//4}:{H//4},curves=all='0/0 0.72/0 1/1',gblur=sigma=5,"
         f"colorchannelmixer=rr=1:gg=0.42:bb=0.18,scale={W}:{H}:flags=bilinear,format=gbrp[glow];"
         "[base][glow]blend=all_mode=screen:all_opacity=0.32[hal];"
         # film response: lifted blacks, rolled highlights, cold shadows, warm highlights, less saturation
         "[hal]curves=all='0/0.03 0.25/0.21 0.5/0.47 0.8/0.80 1/0.95',"
         "colorbalance=rs=-0.03:gs=0.0:bs=0.035:rh=0.025:gh=0.0:bh=-0.03,"
         "eq=saturation=0.86,"
         # take the digital edge off, then grain and a soft vignette
         "gblur=sigma=0.55,noise=alls=7:allf=t,vignette=angle=PI/5.5,format=yuv420p[vout]")
if a.light:
    grade = "[vcat]format=gbrp,gblur=sigma=0.4,noise=alls=6:allf=t,vignette=angle=PI/6,format=yuv420p[vout]"
if a.nograde:
    grade = "[vcat]format=yuv420p[vout]"
fc = ";".join(vparts + aparts) + ";" + \
     f"{vcat}concat=n={n+1}:v=1:a=0[vcat];" + grade + ";" + \
     f"{acat}concat=n={n+1}:v=0:a=1,highpass=f=70,acompressor=threshold=0.2:ratio=3:attack=5:release=120,volume=0.32[amb];" + \
     f"[{nar}:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=out:st={round(CLIP_OUT-CLIP_IN-0.35,3)}:d=0.35,asplit[nar1][nar2];" + \
     "[amb][nar2]sidechaincompress=threshold=0.03:ratio=4:attack=15:release=350[ambd];" + \
     "[nar1][ambd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[aout]"
cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
       "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-tune", "grain", "-maxrate", "16M", "-bufsize", "32M", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
       "-c:a", "aac", "-b:a", "192k", "-shortest", a.out]
subprocess.run(cmd, check=True)
print("wrote", a.out)
