#!/usr/bin/env python3
"""Fia's Mahjong Collection — VO-driven reel builder.

Differs from the original pipeline/build_shotlist.py:
  - No BPM/beat-grid. Timing is driven by VO segment durations.
  - Audio bed is the concatenated host VO + optional music ducked underneath.
  - Mac-friendly: emits a render_reel.sh that uses h264_videotoolbox (no NVENC).
"""

from pathlib import Path
import csv, textwrap

ROOT  = Path(__file__).parent
SRC   = ROOT / "01-source"
EDIT  = ROOT / "04-edit"
RNDR  = ROOT / "05-renders"
MUSIC = ROOT / "03-music/bed.wav"   # optional ambient bed; set None to skip

# -------- caption text per slot role (drawn at bottom of frame) --------
# `None` skips the caption for that slot.
CAPTIONS = {
    "hook":    None,
    "reveal":  None,
    "tiles":   None,
    "mats":    None,
    "pushers": None,
    "racks":   None,
    "value":   None,
    "cta":     None,
    "end":     None,
}

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
CAPTION_DIR = Path(__file__).parent / "04-edit/captions"
CAPTION_BOTTOM_PAD = 180   # px above the bottom edge (IG safe area)


def caption_height(text):
    """Pixel height for the caption band based on number of lines."""
    return 130 if "\n" not in text else 220


def build_caption_pngs():
    """Render one PNG per unique caption text using ImageMagick. Returns dict role→path."""
    import subprocess
    CAPTION_DIR.mkdir(parents=True, exist_ok=True)
    paths = {}
    for role, text in CAPTIONS.items():
        if not text:
            continue
        out = CAPTION_DIR / f"{role}.png"
        h = caption_height(text)
        subprocess.run([
            "magick",
            "-background", "rgba(0,0,0,0.6)",
            "-fill", "white",
            "-font", FONT_PATH,
            "-pointsize", "56",
            "-gravity", "center",
            "-interline-spacing", "16",
            "-size", f"1080x{h}",
            f"caption:{text}",
            f"PNG32:{out}",
        ], check=True)
        paths[role] = out.relative_to(Path(__file__).parent)
    return paths


def caption_overlay_y(role):
    """Y coordinate where the caption PNG should sit on a 1920-tall frame."""
    text = CAPTIONS.get(role) or ""
    return 1920 - caption_height(text) - CAPTION_BOTTOM_PAD

# -------- VO sequence: each entry = a sentence delivered by the host --------
# (clip_file, src_in, src_out, line_label, line_text)
# (clip, src_in, src_out, line_label, line_text, gap_after_secs)
# gap_after is a brief silence appended after the sentence so the VO breathes naturally
VO = [
    ("IMG_3794.MOV", 1.78, 5.05,  "hook",     "The most beautiful mahjong set is finally here",                       0.40),
    ("IMG_3797.MOV", 0.93, 3.36,  "reveal",   "Introducing a new collection to Fia's Lounge",                        0.40),
    ("IMG_3800.MOV", 3.35, 10.97, "products", "premium tiles, velvet mats, smooth pushers, beautifully crafted racks", 0.40),
    ("IMG_3804.MOV", 1.43, 5.72,  "value",    "Designed to bring elegance, style and comfort in every game",          0.40),
    ("IMG_3807.MOV", 0.96, 4.49,  "cta",      "Visit our website to explore the full collection",                     0.00),
]

# -------- Visual cut sequence --------
# Each cut sits on the timeline relative to the cumulative VO start of its segment.
# (vo_index, sub_offset, sub_duration, role, force_file, force_src_in, label)
#   vo_index   -- which VO segment this visual is laid over
#   sub_offset -- seconds after that VO segment's start
#   sub_dur    -- visual duration on the timeline
# Sub-cuts within a single VO segment chain back-to-back (e.g. 4 product cuts under one VO).
CUTS = [
    # ===== HOOK (under VO #0, 3.27s) — IMG_3794 lip-synced (visual src matches audio src) =====
    (0, 0.00, 3.27, "hook",    "IMG_3794.MOV", 1.78, "Host IMG_3794 (synced to line, slate skipped)"),

    # ===== REVEAL (under VO #1, 2.43s + 0.4s breath) — wide setup =====
    # IMG_3820 is only 2.5s, too short once we extend through the breath gap.
    # IMG_3824 (7.17s) holds easily; CTA opener below uses a later src_in inside the same clip.
    (1, 0.00, 2.43, "reveal",  "IMG_3824.MOV", 0.0,  "Blue pagoda angled — reveal (first window)"),

    # ===== PRODUCT BEATS (under VO #2 "products", 7.62s) — 4 cuts on real speech bursts =====
    # Within trimmed VO #2 (0 = source 3.35):
    #   0.00-1.49  "premium mahjong tiles"   + pause to 1.93
    #   1.93-4.27  "velvet mats, smooth pushers"   (combined burst, no clean split)
    #   4.74-7.62  "and beautifully crafted mahjong racks"
    (2, 0.00, 1.93, "tiles",   "IMG_3833.MOV", 0.5,  "Tile row detail (on 'premium tiles')"),
    (2, 1.93, 1.17, "mats",    "IMG_3818.MOV", 0.0,  "Gold dragon mat (on 'velvet mats')"),
    (2, 3.10, 1.64, "pushers", "IMG_3819.MOV", 0.5,  "Pusher (on 'smooth pushers')"),
    (2, 4.74, 2.88, "racks",   "IMG_3830.MOV", 0.5,  "3-color rack showcase (on 'mahjong racks')"),

    # ===== VALUE (under VO #3, 4.29s) — host back, full sentence incl. "in every game" =====
    (3, 0.00, 4.29, "value",   "IMG_3804.MOV", 1.43, "Host: 'Designed to bring elegance, style and comfort in every game'"),

    # ===== CTA (under VO #4, 3.53s) — split: pagoda first, short site-scroll at the end =====
    (4, 0.00, 1.90, "cta",     "IMG_3824.MOV",   4.0,  "Blue pagoda angled — CTA opener (later window)"),
    (4, 1.90, 1.63, "cta",     "WEBSITE_SCROLL", 0.0,  "Short site scroll: mahjongatfias.in"),

    # ===== LOGO END CARD (post-VO, 1.5s) — silent fade =====
    (None, 0.00, 1.50, "end",  "LOGO_END_CARD", 0.0, "Brand card fade-out"),
]

# -------- compute timeline --------
def vo_dur(i):
    """Audible portion + breathing gap appended after the line."""
    f, s_in, s_out, _lab, _txt, gap = VO[i]
    return max(0.0, s_out - s_in) + gap

vo_starts = [0.0]
for i in range(len(VO)):
    vo_starts.append(vo_starts[-1] + vo_dur(i))

vo_total = vo_starts[-1]
# end-card sits after VO ends
post_offset = vo_total

# Find the last cut for each VO segment so we can extend it across that
# segment's gap_after silence. Visuals hold while the audio breathes.
last_cut_for_vo = {}
for idx, cut in enumerate(CUTS):
    vo_i = cut[0]
    if vo_i is not None:
        last_cut_for_vo[vo_i] = idx

slots = []
for idx, cut in enumerate(CUTS):
    vo_i, sub_o, sub_d, role, ff, src_in, label = cut
    if vo_i is None:
        tl_in = post_offset
        post_offset += sub_d
    else:
        tl_in = vo_starts[vo_i] + sub_o
        if last_cut_for_vo[vo_i] == idx:
            sub_d += VO[vo_i][5]   # gap_after — hold visual through the breath
    tl_out = tl_in + sub_d
    slots.append(dict(
        tl_in=round(tl_in, 3), tl_out=round(tl_out, 3),
        role=role, file=ff, src_in=src_in, label=label, dur=round(sub_d, 3),
    ))

reel_total = post_offset

# -------- sanity check: every visual slot must fit inside its source clip --------
SRC_DUR = {row["filename"]: float(row["duration_sec"])
           for row in csv.DictReader(open(SRC/"inventory.csv"))}
for s in slots:
    if s["file"] in ("LOGO_END_CARD", "WEBSITE_SCROLL"):
        continue
    avail = SRC_DUR[s["file"]] - s["src_in"]
    assert avail >= s["dur"] - 0.05, (
        f"slot {s['role']}: needs {s['dur']:.2f}s from {s['file']} at src_in={s['src_in']:.2f}, "
        f"only {avail:.2f}s available (source clip is {SRC_DUR[s['file']]:.2f}s)"
    )

# -------- write shotlist.csv --------
EDIT.mkdir(parents=True, exist_ok=True)
with open(EDIT/"shotlist.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["slot", "tl_in", "tl_out", "duration", "role", "file", "src_in", "label"])
    for i, s in enumerate(slots):
        w.writerow([i, s["tl_in"], s["tl_out"], s["dur"], s["role"], s["file"], s["src_in"], s["label"]])

# -------- write shotlist.md --------
with open(EDIT/"shotlist.md", "w") as f:
    f.write(f"# Reel timeline ({reel_total:.2f}s total)\n\n")
    f.write("| Slot | TL in | TL out | Dur | Role | File | Src in | Note |\n|---|---|---|---|---|---|---|---|\n")
    for i, s in enumerate(slots):
        f.write(f"| {i} | {s['tl_in']:.2f} | {s['tl_out']:.2f} | {s['dur']:.2f} | {s['role']} | {s['file']} | {s['src_in']:.2f} | {s['label']} |\n")
    f.write("\n## VO bed\n\n")
    f.write("| # | Clip | src_in | src_out | Dur | Line |\n|---|---|---|---|---|---|\n")
    for i, (clip, sin, sout, lab, txt, gap) in enumerate(VO):
        f.write(f"| {i} | {clip} | {sin:.2f} | {sout:.2f} | {sout-sin:.2f} | +{gap:.2f}s breath | {txt} |\n")

# -------- write render_reel.sh (VideoToolbox / Mac) --------
render = f"""#!/usr/bin/env bash
# Generated by build_reel.py — Mac VideoToolbox render
set -euo pipefail
cd "$(dirname "$0")/.."

SRC=01-source
TMP=04-edit/tmp_slots
LOGO=03-music/assets/logo_mahjong_fias.png
SITE=03-music/assets/site_mahjongatfias.png
MUSIC={MUSIC}
OUT=05-renders/reel_v9.mp4

mkdir -p "$TMP"
rm -f "$TMP"/slot_*.mp4 "$TMP"/vo_*.wav "$TMP"/vo_concat.wav

# ---------- Pass 1: render each visual slot (1080x1920, silent) ----------
"""
# Generate all caption PNGs up front (read by overlay below)
caption_paths = build_caption_pngs()

for i, s in enumerate(slots):
    fps = 30
    n_frames = max(1, int(round(s["dur"] * fps)))
    cap_path = caption_paths.get(s["role"])
    cap_y = caption_overlay_y(s["role"])
    if s["file"] == "LOGO_END_CARD":
        render += textwrap.dedent(f"""\
        # slot {i}: logo end card (black bg + centered logo + fade)
        ffmpeg -y -v error -f lavfi -i "color=c=black:s=1080x1920:d={s['dur']}:r={fps}" \\
          -i "$LOGO" \\
          -filter_complex "[1:v]scale=600:-1[lg];[0:v][lg]overlay=(W-w)/2:(H-h)/2,fade=t=out:st={max(0, s['dur']-0.7)}:d=0.7,format=yuv420p" \\
          -c:v h264_videotoolbox -b:v 8M -frames:v {n_frames} "$TMP/slot_{i:03d}.mp4"
        """)
    elif s["file"] == "WEBSITE_SCROLL":
        # Animated scroll of the captured site PNG (+ optional caption overlay)
        scroll_chain = (
            f"[0:v]scale=1080:-2,"
            f"crop=w=1080:h=1920:x=0:y='min((ih-1920)*t/{s['dur']}\\,(ih-1920))':exact=1,"
            f"fps={fps}"
        )
        if cap_path:
            full_filter = f"{scroll_chain}[bg];[bg][1:v]overlay=0:{cap_y}:format=auto,format=yuv420p[v]"
            inputs = f'-loop 1 -t {s["dur"]} -i "$SITE" -i "{cap_path}"'
        else:
            full_filter = f"{scroll_chain},format=yuv420p[v]"
            inputs = f'-loop 1 -t {s["dur"]} -i "$SITE"'
        render += textwrap.dedent(f"""\
        # slot {i}: {s['role']} — animated site scroll over {s['dur']:.2f}s ({s['label']})
        ffmpeg -y -v error {inputs} \\
          -filter_complex "{full_filter}" -map "[v]" \\
          -c:v h264_videotoolbox -b:v 10M -frames:v {n_frames} "$TMP/slot_{i:03d}.mp4"
        """)
    else:
        if cap_path:
            full_filter = (
                f"[0:v]crop=ih*9/16:ih,scale=1080:1920,setsar=1,fps={fps}[bg];"
                f"[bg][1:v]overlay=0:{cap_y}:format=auto,format=yuv420p[v]"
            )
            inputs = f'-ss {s["src_in"]} -i "$SRC/{s["file"]}" -i "{cap_path}"'
            render += textwrap.dedent(f"""\
            # slot {i}: {s['role']} — {s['file']} src_in={s['src_in']} dur={s['dur']} ({s['label']})
            ffmpeg -y -v error {inputs} -an \\
              -filter_complex "{full_filter}" -map "[v]" \\
              -c:v h264_videotoolbox -b:v 12M -frames:v {n_frames} "$TMP/slot_{i:03d}.mp4"
            """)
        else:
            render += textwrap.dedent(f"""\
            # slot {i}: {s['role']} — {s['file']} src_in={s['src_in']} dur={s['dur']} ({s['label']})
            ffmpeg -y -v error -ss {s['src_in']} -i "$SRC/{s['file']}" \\
              -an -vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1,fps={fps},format=yuv420p" \\
              -c:v h264_videotoolbox -b:v 12M -frames:v {n_frames} "$TMP/slot_{i:03d}.mp4"
            """)

# ---------- Pass 1b: extract & concat VO segments ----------
render += "\n# ---------- VO bed: extract each line, append a breathing gap, concat ----------\n"
for i, (clip, sin, sout, lab, txt, gap) in enumerate(VO):
    if sout > sin:
        # apad pads silence at the END to length = (audio duration + gap)
        # We re-encode here (not stream copy) because apad needs a filter pipeline.
        render += (
            f"ffmpeg -y -v error -ss {sin} -to {sout} -i \"$SRC/{clip}\" -vn "
            f"-af \"apad=pad_dur={gap}\" "
            f"-ac 2 -ar 48000 -c:a pcm_s16le \"$TMP/vo_{i:02d}.wav\"\n"
        )
render += "(cd \"$TMP\" && ls vo_*.wav | awk '{print \"file \"$0}' > vo_concat.txt)\n"
render += "ffmpeg -y -v error -f concat -safe 0 -i \"$TMP/vo_concat.txt\" -c copy \"$TMP/vo_concat.wav\"\n"

# ---------- Pass 2: concat slots + audio mix + logo watermark ----------
render += textwrap.dedent("""

# ---------- Pass 2: concat visuals, mux audio ----------
(cd "$TMP" && ls slot_*.mp4 | awk '{print "file "$0}' > slots_concat.txt)

if [ -f "$MUSIC" ]; then
  # VO over music bed (music ducked by sidechain compressor)
  ffmpeg -y -v error \\
    -f concat -safe 0 -i "$TMP/slots_concat.txt" \\
    -i "$TMP/vo_concat.wav" \\
    -i "$MUSIC" \\
    -filter_complex "[2:a]aloop=loop=-1:size=2e9,atrim=duration=REEL_DUR,highpass=f=250,volume=0.07[bed]; \\
                     [1:a]volume=1.0[vo]; \\
                     [vo]asplit=2[vo_mix][vo_sc]; \\
                     [bed][vo_sc]sidechaincompress=threshold=0.02:ratio=20:attack=2:release=350[ducked]; \\
                     [ducked][vo_mix]amix=inputs=2:duration=first:weights=1 8:normalize=0[mix1]; \\
                     [mix1]loudnorm=I=-16:LRA=11:TP=-1.5[mix]" \\
    -map 0:v -map "[mix]" \\
    -c:v copy -c:a aac -b:a 192k -movflags +faststart \\
    "$OUT"
else
  # VO only
  ffmpeg -y -v error \\
    -f concat -safe 0 -i "$TMP/slots_concat.txt" \\
    -i "$TMP/vo_concat.wav" \\
    -af "loudnorm=I=-16:LRA=11:TP=-1.5" \\
    -map 0:v -map 1:a \\
    -c:v copy -c:a aac -b:a 192k -movflags +faststart \\
    "$OUT"
fi
echo "✅ Wrote $OUT"
""").replace("REEL_DUR", f"{reel_total:.2f}")

(EDIT/"render_reel.sh").write_text(render)
(EDIT/"render_reel.sh").chmod(0o755)

print(f"✅ wrote {EDIT/'shotlist.csv'}")
print(f"✅ wrote {EDIT/'shotlist.md'}")
print(f"✅ wrote {EDIT/'render_reel.sh'}")
print(f"Total reel duration: {reel_total:.2f}s  ({len(slots)} slots)")
print(f"VO bed: {vo_total:.2f}s  ({len(VO)} segments)")
