#!/usr/bin/env python3
"""Build the 30-sec Cherry Cherry Lady reel shot list from inventory + classification + beat grid.

Outputs:
  - shotlist.csv  (machine-readable, one row per cut)
  - shotlist.md   (human plan)
  - render_reel.sh  (ffmpeg one-shot: NVENC stitch + music + LUFS norm)
  - resolve_import.py  (DaVinci Resolve scripting to materialize the timeline)
"""

import csv
import json
import textwrap
from pathlib import Path

ROOT = Path("/home/piyushmishra/projects/MothersDay-Mahjong-2026")
SRC  = ROOT / "01-source"
EDIT = ROOT / "04-edit"
MUSIC = ROOT / "03-music/cherry_lady_30s_faded.wav"

# ---------- load data ----------
inv = {}
with open(SRC/"inventory.csv") as f:
    for r in csv.DictReader(f):
        # Accept .MOV / .mov for video — case sensitivity in iPhone filenames varies.
        # JPGs are not in inventory.csv (no duration); we synthesize a dummy duration so the
        # picker can include them via force_file and the render script handles them as freeze frames.
        name = r["filename"]
        if not name.lower().endswith((".mov", ".mp4")):
            continue
        try:
            inv[name] = float(r["duration_sec"])
        except ValueError:
            continue

# Add JPG photos to the inventory with an arbitrary "duration" equal to a long ceiling.
# Freeze-frame handling in render_reel.sh ignores src_dur for stills.
import os
for fname in os.listdir(SRC):
    if fname.lower().endswith((".jpg", ".jpeg")):
        inv[fname] = 999.0  # effectively unlimited

cls = {}
with open(ROOT/"02-thumbs/classification.csv") as f:
    for r in csv.DictReader(f):
        cls[r["filename"]] = (r["tag"], int(r.get("confidence", "0") or 0))

exclude = set(open(ROOT/"02-thumbs/exclude.txt").read().split())
# Also exclude the auto-detected shaky clips so the picker can't backfill them.
exclude |= {"IMG_3490.MOV", "IMG_3524.mov", "IMG_3539.MOV", "IMG_3627.MOV"}
beat_grid = json.loads(open(ROOT/"03-music/beat_grid.json").read())

# ---------- pools ----------
def _is_still(name):
    return name.lower().endswith((".jpg", ".jpeg"))

def pool(tag_filter, min_len, sort_by_len_desc=False):
    items = [
        (fn, dur)
        for fn, dur in inv.items()
        if fn not in exclude and not _is_still(fn)
        and cls.get(fn, ("?", 0))[0] in tag_filter and dur >= min_len
    ]
    return sorted(items, key=lambda x: -x[1] if sort_by_len_desc else x[1])

# ---------- shot list (v2) ----------
# Format: (slot_in, slot_out, role, preferred_tags, label, force_file)
# `force_file` overrides the greedy picker. Use None to let the picker choose.
# Beat = 0.534s. 56 beats fit in 30s.
beat = 60 / beat_grid["bpm"]  # 0.534s
def b(n): return round(n * beat, 3)

SHOTS = [
    # ===== v7 OPENING: Fia → Placard reveal → Wide mahjong table → build =====
    (b(0),  b(1),  "open",   ["people"],   "Opening hero: Fia on mic (window light)",         "IMG_3491.MOV"),
    # v9: IMG_3509.JPG placard removed (too still per Piyush). Wide table now leads opening.
    # Wide mahjong table establish — centerpiece + Fia's branding visible on the table
    (b(3),  b(6),  "open",   ["mahjong"],  "Wide mahjong table + Fia's signage",              "IMG_3488.MOV", 0.0),
    # Build into hook (each 2-3 beats) — slot 1 + 3 swapped for shakiness/focus
    (b(6),  b(9),  "build",  ["people"],   "Player seated (tile-arranging hands, steadier)",  "IMG_3479.mov"),  # was IMG_3475
    (b(9),  b(12), "build",  ["mahjong"],  "Tiles being placed / shuffled",                   None),
    # Sec 6-7 swap: was IMG_3497 (Fia, shaky per Piyush) → IMG_3528 (woman chatting w/ game pieces)
    (b(12), b(14), "build",  ["mixed"],    "Table establishing (clean, non-shaky)",           "IMG_3528.MOV"),
    (b(14), b(16), "build",  ["people"],   "Reaction",                                        None),
    # HOOK 1 — rapid-fire single-beat cuts
    (b(16), b(17), "hook1",  ["mahjong"],  "Hook pop: tile slam",                             None),
    (b(17), b(18), "hook1",  ["people"],   "Hook pop: face",                                  None),
    (b(18), b(19), "hook1",  ["mahjong"],  "Hook pop: hand placing",                          None),
    (b(19), b(20), "hook1",  ["people"],   "Hook pop: laugh",                                 None),
    (b(20), b(21), "hook1",  ["mahjong"],  "Hook pop: tile detail",                           None),
    # v9: IMG_3517.JPG fun-pop removed (too still per Piyush). Picker fills with a video clip.
    (b(21), b(22), "hook1",  ["mixed"],    "Hook pop: table action (video, no still)",         None),
    # Brief breath (2 beats)
    (b(22), b(24), "mid",    ["mahjong"],  "Mid hero: longer hold on play",                   None),
    # HOOK 2 — single beats again
    (b(24), b(25), "hook2",  ["people"],   "FUN POP: smiling woman at red rack",              "IMG_3499.MOV"),  # was IMG_3555
    (b(25), b(26), "hook2",  ["mahjong"],  "Hook2: tiles",                                    None),
    (b(26), b(27), "hook2",  ["people"],   "Hook2: face",                                     None),
    (b(27), b(28), "hook2",  ["mahjong"],  "Hook2: hand",                                     None),
    (b(28), b(29), "hook2",  ["mixed"],    "Hook2: tableau",                                  None),
    (b(29), b(30), "hook2",  ["people"],   "Hook2: smile",                                    None),
    # Mid-bridge (2 beats each)
    (b(30), b(32), "mid",    ["mixed"],    "Hostess / wide context",                          None),
    (b(32), b(34), "mid",    ["mahjong"],  "Top-down shuffle hero",                           None),
    # Final hook burst
    (b(34), b(35), "hook3",  ["people"],   "Final pop: reaction",                             None),
    (b(35), b(36), "hook3",  ["mahjong"],  "Final pop: tile",                                 None),
    (b(36), b(37), "hook3",  ["people"],   "Final pop: laugh",                                None),
    (b(37), b(38), "hook3",  ["mahjong"],  "Final pop: play",                                 None),
    (b(38), b(40), "hook3",  ["mixed"],    "Group action 2-beat",                             None),
    # Sec 22 swap: was IMG_3530 (Fia, shaky per Piyush) → IMG_3524 (clean mahjong collaboration)
    (b(40), b(42), "mid",    ["mahjong"],  "Hero detail hold (clean, non-shaky)",             "IMG_3524.mov"),
    # Build to close (faster)
    (b(42), b(43), "close_b", ["people"],  "Close build: face",                               None),
    (b(43), b(44), "close_b", ["mahjong"], "Close build: tile",                               None),
    (b(44), b(45), "close_b", ["people"],  "Close build: smile",                              None),
    (b(45), b(46), "close_b", ["mahjong"], "Close build: hand",                               None),
    (b(46), b(48), "close_b", ["mixed"],   "Wider 2-beat",                                    None),
    # ===== v5 CLOSE: players-action → brand-card reveal → Fia portrait =====
    # IMG_3488's actual useful frames showed buffet, not the brand card — swapped to IMG_3478.
    (b(48), b(50), "close",   ["mahjong"], "Close 1: two players studying tiles up close",     "IMG_3478.MOV"),
    # IMG_3518 trimmed lands on the MAHJONG @ FIA'S LOUNGE MOTHER'S DAY EDITION card.
    (b(50), b(52), "close",   ["mahjong"], "Close 2: brand card reveal (trimmed start)",      "IMG_3518.MOV", 1.065),
    # Closing: branded logo end card — black bg, centered Mahjong @ Fia's Lounge logo,
    # fade in 0.3s -> hold -> fade out 1.0s. Replaces the IMG_3543 photo per Piyush feedback.
    (b(52), 30.0,  "close",   [],          "ENDING: logo end card (fade in/out)",              "LOGO_END_CARD"),
]

# v8: auto-drop slots whose actual encoded content was flagged as too shaky by
# 04-edit/score_shakiness.py (scores > 4.0 in v7). Reel duration shrinks naturally
# and the remaining slots are renumbered to be contiguous in the timeline.
SHAKY_DROP = {
    "IMG_3490.MOV",  # score 4.41 (hook1 people laugh)
    "IMG_3524.mov",  # score 4.34 (mid mahjong — was the "non-shaky" replacement, ironic)
    "IMG_3539.MOV",  # score 8.64 (close_b Fia mic — worst offender)
    "IMG_3627.MOV",  # score 4.33 (close_b wider mixed)
}
# Read v7 shotlist to find slot labels where the picker assigned a shaky clip.
# Drop those slot labels too — otherwise the picker just re-fills them with
# something else next run and the reel doesn't shrink.
_shaky_labels = set()
try:
    with open(EDIT/"shotlist_v7.csv") as _f:
        for _r in csv.DictReader(_f):
            if _r["file"] in SHAKY_DROP:
                _shaky_labels.add(_r["label"])
except FileNotFoundError:
    pass
SHOTS = [
    s for s in SHOTS
    if not (len(s) >= 6 and s[5] in SHAKY_DROP)
    and s[4] not in _shaky_labels
]

# Renumber tl_in / tl_out so the timeline is contiguous after the drops.
_renumbered = []
_t = 0.0
for s in SHOTS:
    _slot_len = round(s[1] - s[0], 3)
    new_in = round(_t, 3)
    new_out = round(_t + _slot_len, 3)
    _renumbered.append((new_in, new_out) + s[2:])
    _t += _slot_len
SHOTS = _renumbered

# ---------- assign clips greedily ----------
used = set()

def pick(tags, slot_len):
    # Prefer in-tag, longest match (gives editor source-in/out flexibility);
    # fall back across tags if pool is exhausted.
    fallback_order = list(tags) + ["mahjong", "mixed", "people"]
    seen = set()
    fallback_order = [t for t in fallback_order if not (t in seen or seen.add(t))]
    for t in fallback_order:
        candidates = [
            (fn, dur) for fn, dur in inv.items()
            if fn not in used and fn not in exclude and not _is_still(fn)
            and cls.get(fn, ("?",0))[0] == t
            and dur >= slot_len - 0.05  # tiny tolerance
        ]
        if candidates:
            # Pick the LONGEST that fits — gives editor room to choose source in/out
            candidates.sort(key=lambda x: -x[1])
            fn = candidates[0][0]
            used.add(fn)
            return fn, candidates[0][1]
    # absolute fallback: any unused clip long enough (still excluded)
    candidates = [(fn, dur) for fn, dur in inv.items()
                  if fn not in used and fn not in exclude and not _is_still(fn)
                  and dur >= slot_len - 0.05]
    if candidates:
        candidates.sort(key=lambda x: -x[1])
        used.add(candidates[0][0])
        return candidates[0][0], candidates[0][1]
    # nothing fits — allow shortest available even if too short (editor will trim/freeze)
    candidates = [(fn, dur) for fn, dur in inv.items()
                  if fn not in used and fn not in exclude and not _is_still(fn)]
    candidates.sort(key=lambda x: -x[1])
    if candidates:
        used.add(candidates[0][0])
        return candidates[0][0], candidates[0][1]
    return None, 0

# Reserve all force_file entries BEFORE the picking loop so the greedy picker
# never grabs a clip we've explicitly assigned elsewhere in the timeline.
# (Note: same file may legitimately appear in two slots if forced both times — e.g. a clip split
# across two windows. The reservation only blocks the greedy picker, not explicit duplicates.)
for slot in SHOTS:
    if len(slot) >= 6 and slot[5]:
        used.add(slot[5])

assigned = []
for slot in SHOTS:
    # Tuples are 5, 6, or 7 long. 6th = force_file, 7th = explicit src_in override.
    force_file = slot[5] if len(slot) >= 6 else None
    force_src_in = slot[6] if len(slot) >= 7 else None
    slot_in, slot_out, role, tags, label = slot[:5]
    slot_len = round(slot_out - slot_in, 3)
    if force_file:
        fn = force_file
        src_dur = inv.get(fn, slot_len if fn == "LOGO_END_CARD" else 0.0)
        if fn not in used:
            used.add(fn)
    else:
        fn, src_dur = pick(tags, slot_len)
    # Source in/out: stills + end-card sentinels get 0..slot_len; videos honor explicit src_in or center-fit.
    is_still = fn and fn.lower().endswith((".jpg", ".jpeg"))
    is_end_card = fn == "LOGO_END_CARD"
    if is_still or is_end_card:
        src_in, src_out = 0.0, round(slot_len, 3)
    elif force_src_in is not None:
        src_in = round(force_src_in, 3)
        src_out = round(min(src_in + slot_len, src_dur), 3)
    elif src_dur >= slot_len:
        src_in = round((src_dur - slot_len) / 2, 3)
        src_out = round(src_in + slot_len, 3)
    else:
        src_in = 0.0
        src_out = round(src_dur, 3)
    assigned.append({
        "tl_in": slot_in, "tl_out": slot_out, "tl_len": slot_len,
        "role": role, "label": label,
        "file": fn, "src_dur": src_dur,
        "src_in": src_in, "src_out": src_out,
        "tag": cls.get(fn, ("?",0))[0] if fn else "?",
    })

# ---------- write csv ----------
with open(EDIT/"shotlist.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=[
        "tl_in","tl_out","tl_len","role","tag","file","src_dur","src_in","src_out","label"
    ])
    w.writeheader()
    for a in assigned:
        w.writerow(a)

# ---------- write markdown plan ----------
with open(EDIT/"shotlist.md", "w") as f:
    f.write(f"# Mother's Day Mahjong Reel — Shot List\n\n")
    f.write(f"**Song:** Cherry Cherry Lady (Modern Talking)  \n")
    f.write(f"**BPM:** {beat_grid['bpm']:.2f}  \n")
    f.write(f"**Beat:** {beat:.3f}s  \n")
    f.write(f"**Window:** original {beat_grid.get('window_start_sec', 0):.2f}–{beat_grid.get('window_end_sec', 0):.2f}s  \n")
    f.write(f"**Length:** 30.0s vertical 1080×1920, source 3840×2160 landscape (center crop to 9:16)  \n")
    f.write(f"**Cuts:** {len(assigned)} clips, {len(set(a['file'] for a in assigned))} unique sources  \n")
    f.write(f"**Pool:** {len(inv)-len(exclude)} candidate clips ({len(exclude)} food clips excluded)  \n\n")
    f.write("| TL in | TL out | Len | Role | Tag | Clip | Src in→out | Note |\n")
    f.write("|---|---|---|---|---|---|---|---|\n")
    for a in assigned:
        f.write(f"| {a['tl_in']:.2f} | {a['tl_out']:.2f} | {a['tl_len']:.2f}s | {a['role']} | {a['tag']} | `{a['file']}` | {a['src_in']:.2f}→{a['src_out']:.2f} | {a['label']} |\n")
    f.write("\n## Output\n- 1080×1920 H.264 NVENC CRF 20, AAC 192k, +faststart\n- Audio: cherry_lady_30s_faded.wav (already -16 LUFS, Instagram spec)\n")

# ---------- write two-pass NVENC render script (handles .MOV + .JPG, Ken Burns on closer) ----------
# Pass 1: encode each slot serially (1 source at a time, GPU per-clip, memory-light).
# Pass 2: concat with stream-copy + mux the music. JPG slots use -loop 1 -t LEN -i.
# Apply Ken Burns slow zoom to the LAST slot if it's a still — gives the ending photo motion.
music = ROOT/"03-music/cherry_lady_30s_faded.wav"
logo = ROOT/"03-music/assets/logo_mahjong_fias.png"
script = f'''#!/usr/bin/env bash
# Auto-generated by build_shotlist.py — two-pass NVENC render + logo overlay
set -euo pipefail

ROOT="{ROOT}"
SRC="$ROOT/01-source"
TMP="$ROOT/04-edit/tmp_slots"
OUT="{ROOT/"05-renders/reel_v9.mp4"}"
MUSIC="{music}"
LOGO="{logo}"
SHOTLIST="{EDIT/"shotlist.csv"}"

mkdir -p "$TMP" "$(dirname "$OUT")"
rm -f "$TMP"/*.mp4 "$TMP/concat.txt"

python3 - "$SHOTLIST" "$SRC" "$TMP" << 'PY'
import csv, sys, subprocess
from pathlib import Path
shotlist, src, tmp = map(Path, sys.argv[1:4])
rows = list(csv.DictReader(open(shotlist)))
concat_lines = []
last_idx = len(rows) - 1
for i, r in enumerate(rows):
    out_file = tmp / f"slot_{{i:03d}}.mp4"
    tl_len = float(r["tl_len"])
    # Use EXACT frame count to avoid NVENC GOP drift accumulating across 30+ slots.
    frames = max(int(round(tl_len * 30)), 1)
    is_end_card = r["file"] == "LOGO_END_CARD"
    if not is_end_card:
        in_file = src / r["file"]
    is_still = (not is_end_card) and in_file.suffix.lower() in (".jpg", ".jpeg")
    is_last_still = is_still and i == last_idx
    # Common video filter — center-crop landscape to 9:16, scale, 30fps
    vf_common = ("crop=ih*9/16:ih,scale=1080:1920:flags=lanczos,"
                 "setsar=1,format=yuv420p,fps=30")
    if is_end_card:
        # Logo end card: black 1080x1920 background + centered logo at 60% width,
        # fade in 0.3s, fade out 1.0s (per Piyush). LOGO env injected from caller.
        fade_out_start = max(tl_len - 1.0, 0.0)
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", f"color=black:s=1080x1920:r=30:d={{tl_len:.3f}}",
            "-loop", "1", "-framerate", "30", "-t", f"{{tl_len:.3f}}",
            "-i", "{logo}",
            "-filter_complex",
            "[1:v]scale=648:-1[lo];"
            "[0:v][lo]overlay=(W-w)/2:(H-h)/2:format=auto,"
            f"fade=t=in:st=0:d=0.3,fade=t=out:st={{fade_out_start:.3f}}:d=1.0,"
            "format=yuv420p",
            "-c:v", "h264_nvenc", "-preset", "p4", "-rc", "cbr",
            "-b:v", "12M", "-maxrate", "12M", "-bufsize", "18M",
            "-r", "30", "-frames:v", str(frames),
            "-an", str(out_file),
        ]
    elif is_still:
        # Stills come in landscape (5712x4284) or portrait — both have aspect > 1080/1920,
        # so scaling height to 1920 always yields a width >= 1080 we can center-crop from.
        still_base = ("scale=-2:1920:flags=lanczos,"
                      "crop=1080:1920:(iw-1080)/2:0,format=yuv420p")
        if is_last_still:
            # Ken Burns slow zoom 1.00 -> 1.15 over the slot.
            # zoompan with d=1 means each input frame produces 1 output frame and
            # the zoom accumulator persists, so total output = (loop input frames).
            zstep = 0.15 / max(frames - 1, 1)
            zoompan = (",zoompan=z='min(zoom+{{zstep:.5f}},1.15)':d=1:"
                       "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                       "s=1080x1920:fps=30").format(zstep=zstep)
            vf = still_base + zoompan
        else:
            vf = still_base + ",fps=30"
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-framerate", "30", "-t", f"{{tl_len:.3f}}",
            "-i", str(in_file),
            "-vf", vf,
            "-c:v", "h264_nvenc", "-preset", "p4", "-rc", "cbr",
            "-b:v", "12M", "-maxrate", "12M", "-bufsize", "18M",
            "-pix_fmt", "yuv420p", "-r", "30",
            "-frames:v", str(frames),
            "-an", str(out_file),
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-hwaccel", "cuda",
            "-ss", r["src_in"], "-t", f"{{tl_len:.3f}}",
            "-i", str(in_file),
            "-vf", vf_common,
            "-c:v", "h264_nvenc", "-preset", "p4", "-rc", "cbr",
            "-b:v", "12M", "-maxrate", "12M", "-bufsize", "18M",
            "-r", "30",
            "-frames:v", str(frames),
            "-an", str(out_file),
        ]
    tag = ''
    if is_end_card: tag = ' [LOGO END CARD]'
    elif is_last_still: tag = ' [STILL] [KEN BURNS]'
    elif is_still: tag = ' [STILL]'
    print(f"[{{i+1}}/{{len(rows)}}] {{r['file']}} ({{tl_len}}s, {{frames}}f){{tag}} ", end="", flush=True)
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FAIL"); print(res.stderr[-600:]); sys.exit(1)
    print("OK")
    concat_lines.append(f"file '{{out_file}}'")
(tmp/"concat.txt").write_text("\\n".join(concat_lines) + "\\n")
PY

# Pass 2: concat all slots + overlay persistent logo (top-right) + mux music, NVENC re-encode.
# Closing photo already has the brand badge in-frame, so no end-card bump needed.
ffmpeg -y -hide_banner -loglevel warning \\
  -f concat -safe 0 -i "$TMP/concat.txt" \\
  -i "$LOGO" \\
  -i "$MUSIC" \\
  -filter_complex "\\
    [1:v]scale=130:-1[lo]; \\
    [0:v][lo]overlay=W-w-32:32:format=auto[vout]" \\
  -map "[vout]" -map 2:a \\
  -c:v h264_nvenc -preset p5 -tune hq -rc vbr -cq 20 -b:v 0 -maxrate 14M -bufsize 21M \\
  -c:a aac -b:a 192k -ar 48000 \\
  -movflags +faststart \\
  -shortest -t 30 \\
  "$OUT"

echo
echo "DONE: $OUT ($(du -h "$OUT" | cut -f1))"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,duration,codec_name -of default=nw=1 "$OUT"
'''

with open(EDIT/"render_reel.sh", "w") as f:
    f.write(script)

# ---------- write Resolve scripting helper ----------
resolve_py = textwrap.dedent(f'''\
    """Import the reel shot list into a fresh DaVinci Resolve timeline.

    Run inside Resolve's Workspace → Console (Python tab) OR with:
      export RESOLVE_SCRIPT_API="/opt/resolve/Developer/Scripting"
      export RESOLVE_SCRIPT_LIB="/opt/resolve/libs/Fusion/fusionscript.so"
      export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
      python3 resolve_import.py
    Requires Resolve to be open with a project loaded (Studio not required for import).
    """
    import csv, os, sys
    sys.path.append(os.environ.get("RESOLVE_SCRIPT_API","") + "/Modules/")
    import DaVinciResolveScript as dvr

    SRC_DIR = "{SRC}"
    SHOTLIST = "{EDIT/"shotlist.csv"}"
    MUSIC = "{MUSIC}"

    resolve = dvr.scriptapp("Resolve")
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() or pm.CreateProject("MothersDay_Mahjong_Reel")
    mp = project.GetMediaPool()
    ms = resolve.GetMediaStorage()
    root = mp.GetRootFolder()

    # Bin
    bin_clips = mp.AddSubFolder(root, "01_Clips")
    bin_music = mp.AddSubFolder(root, "02_Music")

    # Import the unique source clips and the music
    rows = list(csv.DictReader(open(SHOTLIST)))
    unique = sorted(set(r["file"] for r in rows))
    mp.SetCurrentFolder(bin_clips)
    ms.AddItemListToMediaPool([os.path.join(SRC_DIR, f) for f in unique])
    mp.SetCurrentFolder(bin_music)
    ms.AddItemListToMediaPool([MUSIC])

    # Lookup clips by file name
    clip_by_name = {{}}
    for c in bin_clips.GetClipList():
        clip_by_name[c.GetClipProperty("File Name")] = c

    # Empty 1080x1920 30fps timeline
    project.SetSetting("timelineResolutionWidth", "1080")
    project.SetSetting("timelineResolutionHeight", "1920")
    project.SetSetting("timelineFrameRate", "30")
    timeline = mp.CreateEmptyTimeline("Mahjong_Reel_30s")

    fps = 30
    items = []
    for r in rows:
        clip = clip_by_name.get(r["file"])
        if not clip:
            continue
        start = int(float(r["src_in"]) * fps)
        end   = int(float(r["src_out"]) * fps)
        items.append({{
            "mediaPoolItem": clip,
            "startFrame": start,
            "endFrame": end,
            "trackIndex": 1,
            "mediaType": 1,
        }})
    mp.AppendToTimeline(items)

    # Add the music to audio track 1
    music_clip = next(iter(bin_music.GetClipList()), None)
    if music_clip:
        mp.AppendToTimeline([{{"mediaPoolItem": music_clip, "trackIndex": 1, "mediaType": 2}}])

    print(f"Imported {{len(items)}} clips + music. Timeline 'Mahjong_Reel_30s' ready.")
''')

with open(EDIT/"resolve_import.py", "w") as f:
    f.write(resolve_py)

# ---------- final report ----------
unique_clips = len(set(a["file"] for a in assigned))
total_len = sum(a["tl_len"] for a in assigned)
short_falls = [a for a in assigned if a["src_dur"] < a["tl_len"] - 0.05]
print(f"Shot list: {len(assigned)} cuts, {unique_clips} unique sources, total {total_len:.2f}s")
print(f"Files written under {EDIT}/")
print("  - shotlist.csv")
print("  - shotlist.md")
print("  - render_reel.sh  (ffmpeg one-shot via NVENC)")
print("  - resolve_import.py  (DaVinci Resolve scripting)")
if short_falls:
    print(f"⚠ {len(short_falls)} slot(s) had no clip long enough — editor should pick alts or freeze-frame:")
    for a in short_falls:
        print(f"   slot {a['tl_in']:.2f}–{a['tl_out']:.2f} ({a['role']}/{a['tag']}): {a['file']} only {a['src_dur']:.2f}s")
