"""A2 cut: the review's fixes applied.
- frame-accurate: every shot is cut on exact frame numbers on the narration clock (no drift)
- S2 new take (nothing thrown in), S4 + S8 from one new take of the same bundle (no stick, no body shape)
- S3 hoods softened where the fabric formed a face; S7 lifted to sit with its neighbours
- continuous rain bed under the whole scene, so the ambience never drops out at a cut
python3 edit2.py OUT.mp4
"""
import subprocess, sys

OUT = sys.argv[1]
W, H, FPS = 1920, 1080, 24
CLIP_IN, CLIP_OUT = 96.6, 119.3
# id, source, in-point (s), first frame, end frame (on the scene clock), brightness, saturation
SHOTS = [
    ("S1", "clips/S1_v1.mp4", 0.60,   0, 125,  0.00, 1.00),
    ("S2", "clips/S2_L1.mp4", 0.00, 125, 221, -0.02, 0.92),
    ("S3", "clips/S3_v1.mp4", 1.20, 221, 281, -0.02, 0.95),
    ("S4", "clips/S8_L1.mp4", 0.00, 281, 338, -0.03, 0.92),
    ("S5", "clips/S5_v1.mp4", 1.50, 338, 384, -0.03, 0.90),
    ("S6", "clips/S6_v1.mp4", 1.40, 384, 439, -0.02, 0.90),
    ("S7", "clips/S7_v1.mp4", 1.80, 439, 478,  0.045, 1.00),
    ("S8", "clips/S8_L1.mp4", 2.40, 478, 514, -0.04, 0.90),
]
END = 545  # black tail to 22.7 s
inputs, vp, ap = [], [], []
for i, (sid, src, t0, a, b, br, sat) in enumerate(SHOTS):
    n = b - a
    f0 = round(t0 * FPS)
    inputs += ["-i", src]
    chain = (f"[{i}:v]fps={FPS},trim=start_frame={f0}:end_frame={f0 + n},setpts=PTS-STARTPTS,"
             f"scale={W}:{H}:flags=lanczos,setsar=1")
    if sid == "S7":
        chain += f",eq=brightness={br}:saturation={sat}:gamma=1.12"
    else:
        chain += f",eq=brightness={br}:saturation={sat}"
    if sid == "S8":  # slow push-in over the shot, done at 2x to avoid pixel stepping
        chain += (f",scale={W*2}:{H*2}:flags=bicubic,zoompan=z='1+0.10*on/{n}':x='iw/2-(iw/zoom/2)':"
                  f"y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
    if sid == "S3":  # soften the two foreground hoods (face-like dimples); mask = feathered ellipses
        vp.append(chain + f",split[s3a][s3b]")
        vp.append(f"[s3b]gblur=sigma=16[s3blur]")
        vp.append(f"[hoodmask]scale={W}:{H},format=gray,loop=loop=-1:size=1,trim=end_frame={n},setpts=PTS-STARTPTS[hm]")
        vp.append(f"[s3blur][hm]alphamerge[s3top]")
        vp.append(f"[s3a][s3top]overlay=format=auto[v{i}]")
    else:
        vp.append(chain + f"[v{i}]")
    ap.append(f"[{i}:a]atrim=start_sample={int(t0*48000)}:end_sample={int((t0 + n / FPS)*48000)},"
              f"asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
              f"afade=t=in:d=0.03,afade=t=out:st={n / FPS - 0.03:.3f}:d=0.03[a{i}]")
k = len(SHOTS)
tail = (END - SHOTS[-1][4]) / FPS
total = END / FPS
vp.append(f"color=c=black:s={W}x{H}:r={FPS}:d={tail:.4f},setsar=1[vb]")
ap.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={tail:.4f}[ab]")
inputs += ["-loop", "1", "-i", "qa/hoodmask.png"]; mask_i = k
inputs += ["-ss", "12", "-i", "sfx/1262.mp3"]; rain_i = k + 1
inputs += ["-ss", str(CLIP_IN), "-t", f"{CLIP_OUT - CLIP_IN:.3f}", "-i", "audio/episode.mp3"]; nar_i = k + 2
vp = [v.replace("[hoodmask]", f"[{mask_i}:v]") for v in vp]

grade = ("[vcat]format=gbrp,split[base][hl];"
         f"[hl]scale={W//4}:{H//4},curves=all='0/0 0.72/0 1/1',gblur=sigma=5,"
         f"colorchannelmixer=rr=1:gg=0.42:bb=0.18,scale={W}:{H}:flags=bilinear,format=gbrp[glow];"
         "[base][glow]blend=all_mode=screen:all_opacity=0.32[hal];"
         "[hal]curves=all='0/0.03 0.25/0.21 0.5/0.47 0.8/0.80 1/0.95',"
         "colorbalance=rs=-0.03:gs=0.0:bs=0.035:rh=0.025:gh=0.0:bh=-0.03,"
         "eq=saturation=0.86,gblur=sigma=0.55,noise=alls=7:allf=t,vignette=angle=PI/5.5,format=yuv420p[vout]")
fc = ";".join(vp + ap) + ";" + \
     "".join(f"[v{i}]" for i in range(k)) + f"[vb]concat=n={k+1}:v=1:a=0[vcat];" + grade + ";" + \
     "".join(f"[a{i}]" for i in range(k)) + f"[ab]concat=n={k+1}:v=0:a=1,highpass=f=70," \
     "acompressor=threshold=0.2:ratio=3:attack=5:release=120,volume=0.30[amb];" + \
     f"[{rain_i}:a]atrim=duration={total:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo," \
     f"lowpass=f=8500,volume=0.13,afade=t=in:d=0.8,afade=t=out:st={total-1.2:.3f}:d=1.2[rain];" + \
     "[amb][rain]amix=inputs=2:duration=longest:normalize=0[bed];" + \
     f"[{nar_i}:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=out:st={CLIP_OUT-CLIP_IN-0.35:.3f}:d=0.35,asplit[n1][n2];" + \
     "[bed][n2]sidechaincompress=threshold=0.03:ratio=4:attack=15:release=350[bedd];" + \
     "[n1][bedd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[aout]"
cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
       "-frames:v", str(END), "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-tune", "grain",
       "-maxrate", "16M", "-bufsize", "32M", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
       "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", OUT]
subprocess.run(cmd, check=True)
print("wrote", OUT, END, "frames")
