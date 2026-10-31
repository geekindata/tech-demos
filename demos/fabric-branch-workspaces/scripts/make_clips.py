"""Cut and blur the three demo clips. Regions are fractions of the frame (all sources are 16:10).
Blur: strong Gaussian (two gblur passes) on the address bar, the status bar commit hash and, in the
update clip, the compare header commit hash. Then a second pass (scripts/blur_names.py) blurs workspace names and any email. Sai's display name and the
public geekindata GitHub org stay visible."""
import subprocess, sys
RAW = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "raw")
ADDR = (0.06, 0.034, 0.915, 0.069)
HASH_STATUS = (0.235, 0.938, 0.305, 0.970)
HASH_HEADER = (0.455, 0.188, 0.565, 0.218)
CLIPS = {
  "clip-branch-out.mp4": ("session-steps5-7.mp4", 1280, 800,
      [(208, 218), (224, 236), (258, 263), (270, 276), (294, 304)], [ADDR, HASH_STATUS]),
  "clip-compare-commit.mp4": ("session-steps9-10.mp4", 1280, 800,
      [(69, 83), (89, 95), (119, 131)], [ADDR, HASH_STATUS]),
  "clip-update-from-git.mp4": ("session-steps12-14-recovered.mp4", 1920, 1200,
      [(52, 57), (89, 105), (166, 172), (182, 196), (219, 225)], [ADDR, HASH_STATUS, HASH_HEADER]),
}
def box(r, W, H):
    x0, y0, x1, y1 = r
    x, y = int(x0 * W) // 2 * 2, int(y0 * H) // 2 * 2
    return x, y, (int(x1 * W) - x) // 2 * 2, (int(y1 * H) - y) // 2 * 2
def blur_chain(inp, regions, W, H, tag):
    f, cur = [], inp
    for i, r in enumerate(regions):
        x, y, w, h = box(r, W, H)
        f.append(f"[{cur}]split[{tag}m{i}][{tag}s{i}];[{tag}s{i}]crop={w}:{h}:{x}:{y},gblur=sigma=24:steps=6,gblur=sigma=24:steps=6[{tag}b{i}];"
                 f"[{tag}m{i}][{tag}b{i}]overlay={x}:{y}[{tag}v{i}]")
        cur = f"{tag}v{i}"
    return ";".join(f), cur
if __name__ == "__main__":
    out = RAW + "/clips/final/"
    for name, (src, W, H, segs, regions) in CLIPS.items():
        if len(sys.argv) > 1 and name not in sys.argv[1:]: continue
        parts = [f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[t{i}]" for i, (a, b) in enumerate(segs)]
        cat = "".join(f"[t{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0[c]"
        bl, last = blur_chain("c", regions, W, H, "x")
        fg = ";".join(parts + [cat, bl, f"[{last}]scale=1280:-2:flags=lanczos,format=yuv420p[out]"])
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", f"{RAW}/{src}", "-filter_complex", fg, "-map", "[out]", "-an",
               "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out + name]
        subprocess.run(cmd, check=True); print("wrote", name, sum(b - a for a, b in segs), "s")
