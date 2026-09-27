"""Cut the cold open: picture from post/SHOT/*.png, sound from the episode plus rain and fire.

usage: python3 assemble.py OUT.mp4 [--label TEXT]
Every shot is fitted to its exact frame count on the episode's clock, so picture
and narration cannot drift.
"""
import os, sys, glob, subprocess, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
FPS = 24
T0, T1 = 94.5, 119.35            # episode seconds: 01:34.50 - 01:59.35
EPISODE = os.path.join(ROOT, "audio/episode.mp3")
RAIN = os.path.join(ROOT, "sfx/1262.mp3")
FIRE = os.path.join(ROOT, "sfx/1330.mp3")
FIRE2 = os.path.join(ROOT, "sfx/1329.mp3")

CUT = [  # shot, start, end (episode seconds)
    ("S1", 94.5, 101.9), ("S2", 101.9, 106.0), ("S3", 106.0, 108.45), ("S4", 108.45, 111.0),
    ("S5", 111.0, 112.8), ("S6", 112.8, 115.15), ("S7", 115.15, 116.6), ("S8", 116.6, 119.35),
]


def fr(t):
    return int(round((t - T0) * FPS))


def build_sequence(tmp):
    os.makedirs(tmp, exist_ok=True)
    k = 0
    for shot, a, b in CUT:
        n = fr(b) - fr(a)
        src = sorted(glob.glob(os.path.join(ROOT, "post", shot, "p_*.png")))
        if not src:
            raise SystemExit(f"missing frames for {shot}")
        for i in range(n):
            p = src[min(i, len(src) - 1)]
            os.symlink(p, os.path.join(tmp, f"{k:05d}.png"))
            k += 1
    return k


def main():
    out = sys.argv[1]
    tmp = os.path.join(ROOT, "tmp_seq")
    shutil.rmtree(tmp, ignore_errors=True)
    n = build_sequence(tmp)
    dur = n / FPS
    # sound levels per shot (dB): rain is loudest on "står ned i stænger", fire rises as we close in
    rain_db = {"S1": -19, "S2": -13, "S3": -18, "S4": -20, "S5": -18, "S6": -21, "S7": -21, "S8": -17}
    fire_db = {"S1": -34, "S2": -17, "S3": -22, "S4": -15, "S5": -21, "S6": -14, "S7": -14, "S8": -30}

    def automation(levels):
        # piecewise volume with 0.25 s ramps between shots
        expr = None
        for shot, a, b in reversed(CUT):
            v = 10 ** (levels[shot] / 20)
            ta, tb = a - T0, b - T0
            seg = f"{v:.4f}"
            expr = seg if expr is None else f"if(lt(t,{tb:.3f}),{seg},{expr})"
        return expr

    fade_out_start = dur - 1.1
    fc = (
        f"[1:a]atrim={T0}:{T1},asetpts=PTS-STARTPTS,afade=t=in:d=0.35,afade=t=out:st={fade_out_start:.3f}:d=1.1,volume=1.0[nar];"
        f"[2:a]atrim=12:{12 + dur},asetpts=PTS-STARTPTS,volume='{automation(rain_db)}':eval=frame,"
        f"afade=t=in:d=1.2,afade=t=out:st={fade_out_start:.3f}:d=1.1,lowpass=f=9000[rain];"
        f"[3:a]aloop=loop=-1:size=2e6,atrim=0:{dur},asetpts=PTS-STARTPTS,volume='{automation(fire_db)}':eval=frame,"
        f"afade=t=out:st={fade_out_start:.3f}:d=1.1[fire];"
        f"[rain][fire]amix=inputs=2:normalize=0[bed];"
        f"[bed][nar]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=300[bedd];"
        f"[bedd][nar]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a];"
        f"[0:v]pad=1280:720:0:92:black,format=yuv420p,fade=t=in:d=1.4,fade=t=out:st={dur - 0.8:.3f}:d=0.8[v]"
    )
    # sidechaincompress consumes [nar] once; split it first
    fc = fc.replace("volume=1.0[nar];", "volume=1.0,asplit=2[nar][nar2];").replace("[bedd][nar]amix", "[bedd][nar2]amix")
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"),
           "-i", EPISODE, "-i", RAIN, "-i", FIRE, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-tune", "grain", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", "-t", f"{dur:.3f}", out]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("wrote", out, f"{dur:.2f}s", n, "frames")


if __name__ == "__main__":
    main()
