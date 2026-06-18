# Example — Fia's Tiles Reel (template remake)

An **exact remake** of a vertical trend template (`Video-533.mp4`): its audio is
borrowed and four Fia's Lounge mahjong-tile shots are dropped into the template's
exact cut slots, producing a 7.73 s vertical reel.

Unlike the `mothers-day-mahjong` example, this project does **not** run BPM/beat
detection — the reference clip's scene cuts *are* the grid.

## What's here

```
fias-tiles-reel/
├── assets/                        dropped clips + extracted audio (gitignored)
├── metadata/
│   ├── template.json              4 slot timings + audio/output spec
│   ├── extract_audio.sh           pulls audio from Video-533.mp4
│   ├── motion_scores.csv          steadiness rank of all 8 candidate clips
│   └── edit_notes.md              template + selection + encode notes
├── shotlists/
│   └── shotlist_template_v1.csv   chosen 4 clips → 4 slots
├── build_template_reel.sh         trim → scale/crop → concat → mux
└── README.md
```

## Re-render

Private/borrowed assets are intentionally excluded (gitignored). To reproduce:

| Asset | Where |
|---|---|
| `Video-533.mp4` | the reference trend clip (private) |
| 8 `IMG_*.MOV` | the Tiles shoot footage (private) |

```bash
# 1. extract the borrowed audio from the reference
bash metadata/extract_audio.sh ~/Downloads/Video-533.mp4

# 2. build (CPU x264 locally; USE_NVENC=1 on the RTX box)
SRC_DIR="$HOME/Downloads/Tiles reel June 26 " bash build_template_reel.sh
# -> reel_v1.mp4  (720×1280, 30fps, 7.64s)
```

## Notes

- Steadiest 4 of 8 clips auto-picked (frame-difference proxy; vidstab unavailable
  locally). IMG_4671 was clearly shaky and dropped. See `metadata/edit_notes.md`.
- Audio is a borrowed trend sound — recipe only, asset not committed.
