# Fia's Tiles Reel — Template Remake

**Date:** 2026-06-18
**Branch:** `add/fias-tiles-reel-template-remake`
**Status:** Design — awaiting review

## Goal

Recreate a reference reel (`Video-533.mp4`) exactly: borrow its audio track and
drop four Fia's Lounge mahjong-tile shots into the reference's exact cut slots,
producing a 7.73 s vertical reel that matches the template beat-for-beat.

## The reference template

`Video-533.mp4` (the trend template) was analysed with ffprobe + scene-cut
detection:

- **Container:** 720×1280, 30 fps, H.264 video + AAC stereo audio
- **Duration:** 7.729 s
- **Structure:** 4 hard-cut shot slots

| Slot | Start (s) | End (s) | Duration (s) |
|------|-----------|---------|--------------|
| 1    | 0.000     | 2.033   | 2.033        |
| 2    | 2.033     | 3.967   | 1.934        |
| 3    | 3.967     | 5.633   | 1.666        |
| 4    | 5.633     | 7.729   | 2.096        |

The audio is the soundtrack of the reference clip. It is a **borrowed sound**,
so — exactly as the `mothers-day-mahjong` example handles its copyrighted track —
the extracted audio is **gitignored**. The repo stores the *recipe* (slot timings,
extraction script), never the asset itself.

## Source footage

Eight vertical iPhone clips delivered in `Tiles reel June 26/` (kept outside the
repo, gitignored). All portrait, rotation −90, 60 fps:

| Clip          | Duration (s) | Resolution  |
|---------------|--------------|-------------|
| IMG_4637.MOV  | 5.86         | 1080×1920   |
| IMG_4639.MOV  | 6.06         | 1080×1920   |
| IMG_4648.MOV  | 5.77         | 2160×3840   |
| IMG_4651.MOV  | 4.28         | 2160×3840   |
| IMG_4652.MOV  | 3.57         | 2160×3840   |
| IMG_4657.MOV  | 4.05         | 1080×1920   |
| IMG_4671.MOV  | 4.88         | 2160×3840   |
| IMG_4677.MOV  | 5.27         | 2160×3840   |

Every clip is longer than the longest slot (2.096 s), so any clip can fill any
slot. There are 8 candidates for 4 slots.

## Clip selection

Auto-pick the **4 steadiest** clips using the repo's `score_shakiness.py`
(vidstabdetect feature-point analysis). Order them shortest-action-first into the
four slots. The chosen 4 and their slot assignment are surfaced to the user for
confirmation **before** the final render.

## Project layout

New folder `examples/fias-tiles-reel/`, mirroring the existing example:

```
fias-tiles-reel/
├── assets/                     dropped clips + logo (gitignored)
├── metadata/
│   ├── template.json           the 4 slot timings + audio spec
│   ├── extract_audio.sh        pulls audio from Video-533.mp4 → template_audio.wav
│   ├── shakiness_scores.csv    vidstabdetect scores for all 8 clips
│   └── edit_notes.md           slot cheat-sheet + selection rationale
├── shotlists/
│   └── shotlist_template_v1.csv   chosen 4 clips → 4 slots (in-point, duration)
├── build_template_reel.sh      per-slot encode + concat + audio mux
└── README.md                   what's here / how to re-render
```

## Render flow

`build_template_reel.sh`:

1. **Extract audio** once from `Video-533.mp4` → `template_audio.wav` (via
   `extract_audio.sh`).
2. **Per slot (1–4):** read the chosen clip + in-point + slot duration from
   `shotlist_template_v1.csv`; trim, apply the −90 rotation, scale-and-crop to
   720×1280, drop to 30 fps, encode each slot to an intermediate `slot_N.mp4`.
3. **Concat** the 4 slots and **mux** `template_audio.wav` (trimmed to 7.729 s).
4. Output `reel_v1.mp4`.

**Encoder:** CPU `libx264` on this Mac (no NVIDIA GPU). NVENC remains the
documented fast path for the RTX box — a `USE_NVENC` flag in the script flips the
encoder. This keeps the branch consistent with the repo's NVENC story while
running locally.

## Pipeline reuse

No changes to the shared `pipeline/` scripts. `score_shakiness.py` is reused as-is
for selection. The template's fixed slot timings replace the BPM-driven
`build_shotlist.py` step (the reference clip *is* the beat grid), so this project
does not run librosa.

## Out of scope

- Beat detection / BPM analysis (the reference clip's cut points are the grid).
- Text overlays, transitions, motion graphics (exact remake = straight cuts).
- Remotion / any non-ffmpeg stack.
- Committing the borrowed audio or the source footage to git.

## Success criteria

- `reel_v1.mp4` is 720×1280, 30 fps, ~7.73 s, with the reference audio.
- Cuts land on the four slot boundaries (0.000 / 2.033 / 3.967 / 5.633).
- The 4 shots are the steadiest of the 8, confirmed by the user before render.
- Repo contains the full recipe; no copyrighted/private assets committed.
