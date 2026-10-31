"""Second blur pass for the published stills and clips: OCR every still, and every clip frame whose
content changed (plus at least every 4th frame, about 0.27 s at 15 fps), then put a strong Gaussian blur on:
- any workspace, item or capacity name, region, GitHub account name, or email (patterns below), and
- any text in the left navigation column that is not a standard nav label (pinned workspaces).
Branch names (fabric-demo-git, fabric-demo-feature) and the UI stay readable.
Usage: python3 blur_names.py shots | clips [name.mp4 ...] | fix name.mp4 ... | verify [filter ...]
Inputs are the first-pass outputs of make_clips.py, kept in raw/shots/stage1 and raw/clips/stage1."""
import os, re, sys, json, subprocess, glob
import cv2, numpy as np
from rapidocr import RapidOCR
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "..", "raw")
OCR = RapidOCR(params={"Global.log_level": "error"})
sys.path.insert(0, HERE); import fab
# Account-, capacity- and region-specific fragments live in env.local (BLUR_EXTRA, comma separated), not in the repo.
try: EXTRA = [re.escape(x.strip().lower()) for x in fab.env("BLUR_EXTRA").split(",") if x.strip()]
except KeyError: EXTRA = []
PAT = re.compile("|".join([r"_w[s5](?![a-z])", r"(?<![a-z])ws_", r"git_w", r"dem\w*w", r"demo_copi", r"demo_agen", r"demo_mirr",
                           r"demo_tri", r"d[e3c][mn][o0]", r"derno", r"dermo", r"overload", r"acdc", r"medallion", r"capacity_metrics", r"fabric_capacity", r"austria",
                           r"fabric_f2", r"fabric_trial", r"trial_lab", r"trial_20", r"premium_per",
                           r"[a-z0-9.]@[a-z0-9]", r"gmail", r"hotmail", r"outlook\."] + EXTRA))
NAV = {"home", "workspaces", "workspace", "power", "bi", "power_bi", "copilot", "power_bi_copilot", "onelake", "catalog",
       "onelake_catalog", "monitor", "real_time", "realtime", "workloads", "my", "my_workspace", "fabric", "apps", "learn",
       "create", "browse", "more", "real", "time", "bi_copilot"}
BRANCH = re.compile(r"fabric_demo_(feature|git)|(?<!gh_)tech_demos")
def norm(t): return BRANCH.sub("", re.sub(r"[\s\-]+", "_", t.lower()).replace("fabric_ws", ""))
def hit(txt, x1, W):
    n = norm(txt)
    if PAT.search(n): return "name"
    if x1 < 0.047 * W:
        k = re.sub(r"[^a-z_]", "", n).strip("_")
        if len(k) >= 3 and not any(w.startswith(k) or k.startswith(w) and len(w) > 3 for w in NAV): return "nav"
    return None
def spans(t):
    """Character spans of a long OCR line to blur. Matching runs on a same-length copy of the line, so spans map back to
    characters. Each match grows to whole words; matches up to one short word apart merge (so "demo git ws feature",
    read with spaces, is blurred as one name), and a short tail after the last match is included."""
    s = re.sub(r"[\s\-]", "_", t.lower()); s = BRANCH.sub(lambda m: " " * len(m.group()), s)
    raw = [(m.start(), m.end()) for m in PAT.finditer(s)]
    if not raw: return []
    sep = lambda i: t[i] in " <>\"',:;()[]{}"
    out = []
    for a, e in raw:
        while a > 0 and not sep(a - 1): a -= 1
        while e < len(t) and not sep(e): e += 1
        if out and a - out[-1][1] <= 10: out[-1] = (out[-1][0], max(e, out[-1][1]))
        else: out.append((a, e))
    a, e = out[-1]
    if len(t) - e <= 10 and len(t) < 40: out[-1] = (a, len(t))
    return out
def detect(img, scales=(2,)):
    H, W = img.shape[:2]; out = []
    for s in scales:
        x = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC) if s != 1 else img
        r = OCR(x)
        if r.boxes is None: continue
        for b, t in zip(r.boxes, r.txts):
            b = np.array(b) / s; x0, y0 = b.min(0); x1, y1 = b.max(0)
            k = hit(t, x1, W)
            if not k: continue
            if k == "name" and len(t) > 12:
                toks = spans(t)
                if toks:
                    cw = (x1 - x0) / max(1, len(t))
                    for a, e in toks:
                        out.append((int(x0 + a * cw - cw), int(y0), int(x0 + e * cw + cw), int(y1), k, t[a:e]))
                    continue
            out.append((int(x0), int(y0), int(x1), int(y1), k, t))
    return out
def blur(img, boxes, pad=6):
    H, W = img.shape[:2]
    for x0, y0, x1, y1, *_ in boxes:
        x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
        if x1 <= x0 or y1 <= y0: continue
        h = y1 - y0; sg = max(10.0, 0.8 * h); m = int(3 * sg)
        X0, Y0, X1, Y1 = max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)
        roi = img[Y0:Y1, X0:X1].copy()
        for _ in range(2): roi = cv2.GaussianBlur(roi, (0, 0), sg)
        img[y0:y1, x0:x1] = roi[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
    return img
def shots():
    log = {}
    for f in sorted(glob.glob(os.path.join(RAW, "shots", "stage1", "*.png"))):
        img = cv2.imread(f); bx = detect(img, (1, 2)); img = blur(img, bx)
        bx2 = detect(img, (1, 2, 3)); img = blur(img, bx2); bx += bx2  # second pass catches names the first boxes missed
        cv2.imwrite(os.path.join(RAW, "shots", "final", os.path.basename(f)), img)
        log[os.path.basename(f)] = [b[4] + ":" + b[5] for b in bx]; print(os.path.basename(f), len(bx), flush=True)
    return log
def changed(a, b, px=600):
    if a is None: return True
    d = cv2.absdiff(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY))
    return int((d > 30).sum()) > px
def clip(name, every=4):
    src = os.path.join(RAW, "clips", "stage1", name); dst = os.path.join(RAW, "clips", "final", name)
    cap = cv2.VideoCapture(src); det = {}; last = None; lastf = -99; i = -1
    while True:
        ok, fr = cap.read()
        if not ok: break
        i += 1
        if i - lastf >= every or changed(last, fr):
            det[i] = detect(fr); last = fr; lastf = i
    n = i + 1; H, W = last.shape[:2]
    keys = sorted(det)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "15",
                          "-i", "-", "-an", "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p",
                          "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
    import bisect
    cap = cv2.VideoCapture(src)
    for i in range(n):
        ok, fr = cap.read()
        j = bisect.bisect_right(keys, i) - 1; bx = list(det[keys[j]])
        if j + 1 < len(keys): bx += det[keys[j + 1]]
        if j - 1 >= 0 and keys[j] == i: bx += det[keys[j - 1]]
        p.stdin.write(blur(fr, bx).tobytes())
    p.stdin.close(); p.wait()
    hits = sorted({b[4] + ":" + b[5] for v in det.values() for b in v})
    print(name, "frames", n, "ocr frames", len(det), "boxes", sum(len(v) for v in det.values()), flush=True)
    return {"frames": n, "ocr_frames": len(det), "texts_blurred": hits}
def fix(name, every=2, win=8):
    """Second pass over a published clip: OCR every 2nd frame of the output, and blur each hit on every frame within
    +-win frames (about 0.5 s), so a name the first pass missed on some frames is covered on all of them."""
    dst = os.path.join(RAW, "clips", "final", name); tmp = dst + ".tmp.mp4"
    cap = cv2.VideoCapture(dst); det = {}; i = -1
    while True:
        ok, fr = cap.read()
        if not ok: break
        i += 1
        if i % every == 0: det[i] = detect(fr)
    n = i + 1; H, W = fr.shape[:2] if fr is not None else (800, 1280)
    cap = cv2.VideoCapture(dst); ok, fr = cap.read(); H, W = fr.shape[:2]; cap = cv2.VideoCapture(dst)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "15",
                          "-i", "-", "-an", "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p",
                          "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    for i in range(n):
        ok, fr = cap.read()
        bx = [b for j in range(i - win, i + win + 1) for b in det.get(j, [])]
        p.stdin.write(blur(fr, bx).tobytes())
    p.stdin.close(); p.wait(); os.replace(tmp, dst)
    hits = sorted({b[4] + ":" + b[5] for v in det.values() for b in v})
    print(name, "frames", n, "ocr frames", len(det), flush=True)
    return {"frames": n, "ocr_frames": len(det), "texts_blurred": hits}
def verify(every=4, only=()):
    keep = lambda f: not only or any(o in os.path.basename(f) for o in only)
    """OCR the published outputs again: report any remaining match, and any account-panel text."""
    res = {}; acct = re.compile(r"sign_out|view_account|switch_account|account_manager|my_account")
    mail = re.compile("|".join([r"@", r"gmail", r"\.com\b"] + EXTRA))
    for f in [x for x in sorted(glob.glob(os.path.join(RAW, "shots", "final", "*.png"))) if keep(x)]:
        img = cv2.imread(f); r = OCR(cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
        txts = list(r.txts or []); W = img.shape[1]
        res[os.path.basename(f)] = {"left": [t for b, t in zip(r.boxes, txts) if hit(t, np.array(b).max(0)[0] / 2, W)],
                                    "account": [t for t in txts if acct.search(norm(t))],
                                    "email": [t for t in txts if mail.search(norm(t))]}
    for f in [x for x in sorted(glob.glob(os.path.join(RAW, "clips", "final", "*.mp4"))) if keep(x)]:
        cap = cv2.VideoCapture(f); i = 0; left = []; ac = []; em = []; n = 0
        while True:
            ok, fr = cap.read()
            if not ok: break
            if i % every == 0:
                r = OCR(cv2.resize(fr, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)); n += 1
                for b, t in zip(r.boxes if r.boxes is not None else [], r.txts or []):
                    if hit(t, np.array(b).max(0)[0] / 2, fr.shape[1]): left.append(f"{i / 15:.2f}s {t}")
                    if acct.search(norm(t)): ac.append(f"{i / 15:.2f}s {t}")
                    if mail.search(norm(t)): em.append(f"{i / 15:.2f}s {t}")
            i += 1
        res[os.path.basename(f)] = {"frames": i, "checked": n, "left": left, "account": ac, "email": em}
    return res
if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "shots": print(json.dumps(shots(), indent=1))
    elif mode == "clips":
        names = sys.argv[2:] or [os.path.basename(x) for x in glob.glob(os.path.join(RAW, "clips", "stage1", "*.mp4"))]
        print(json.dumps({n: clip(n) for n in names}, indent=1))
    elif mode == "fix": print(json.dumps({n: fix(n) for n in sys.argv[2:]}, indent=1))
    elif mode == "verify": print(json.dumps(verify(only=tuple(sys.argv[2:])), indent=1))
