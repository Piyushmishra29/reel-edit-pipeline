#!/usr/bin/env python3
"""Run vidstabdetect on each clip's actual slot window, score shakiness, rank.

Output: shakiness_scores.csv sorted worst→best, plus a printed summary.
"""
import csv, subprocess, math, re, tempfile, os
from pathlib import Path

ROOT = Path("/home/piyushmishra/projects/MothersDay-Mahjong-2026")
SRC  = ROOT / "01-source"
EDIT = ROOT / "04-edit"

rows = list(csv.DictReader(open(EDIT/"shotlist.csv")))
scores = []

for i, r in enumerate(rows):
    fn = r["file"]
    # Skip non-video slots
    if fn == "LOGO_END_CARD" or fn.lower().endswith((".jpg", ".jpeg")):
        continue
    in_file = SRC / fn
    src_in = float(r["src_in"])
    tl_len = float(r["tl_len"])
    with tempfile.TemporaryDirectory() as td:
        trf = Path(td) / "t.trf"
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", str(src_in), "-t", str(tl_len),
            "-i", str(in_file),
            "-vf", f"scale=480:-2,vidstabdetect=shakiness=10:accuracy=15:result={trf}",
            "-f", "null", "-"
        ]
        subprocess.run(cmd, check=True)
        if not trf.exists():
            continue
        # Parse LM (local motion) feature points per frame.
        # Format: (LM dx dy x y size contrast match_quality)
        # Score per frame = mean |dx|+|dy| across all features.
        # Overall score = mean of per-frame scores (a steady clip ~< 2, shaky > 5).
        lm_re = re.compile(r"\(LM\s+(-?\d+)\s+(-?\d+)\s+")
        per_frame_scores = []
        with open(trf) as f:
            for line in f:
                if not line.startswith("Frame "): continue
                feats = lm_re.findall(line)
                if not feats: continue
                disps = [abs(int(dx)) + abs(int(dy)) for dx, dy in feats]
                # Trimmed mean: drop top 10% outliers to ignore weird single features
                disps.sort()
                k = max(1, len(disps) - len(disps)//10)
                per_frame_scores.append(sum(disps[:k]) / k)
        if not per_frame_scores: continue
        score = sum(per_frame_scores) / len(per_frame_scores)
        mean_tx = mean_ty = mean_a = 0  # not used in this scoring
        scores.append({
            "slot": i, "file": fn, "tl_in": r["tl_in"], "tl_len": tl_len,
            "src_in": src_in, "mean_tx": round(mean_tx,3),
            "mean_ty": round(mean_ty,3), "mean_alpha": round(mean_a,5),
            "score": round(score,3), "label": r["label"]
        })

scores.sort(key=lambda x: -x["score"])

out = EDIT / "shakiness_scores.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(scores[0].keys()))
    w.writeheader()
    for s in scores: w.writerow(s)

print(f"Scored {len(scores)} video slots. Top 10 shakiest:\n")
print(f"{'rank':>4}  {'score':>7}  {'slot':>4}  {'tl_in':>6}  {'file':18}  {'label'}")
for rank, s in enumerate(scores[:10], 1):
    print(f"{rank:>4}  {s['score']:>7.2f}  {s['slot']:>4}  {s['tl_in']:>6}  {s['file']:18}  {s['label'][:60]}")
print(f"\nMedian score: {scores[len(scores)//2]['score']:.2f}")
print(f"Output: {out}")
