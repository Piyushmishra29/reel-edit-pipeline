# Example — Mother's Day Mahjong 2026

Working example used to validate the pipeline. **Mahjong tournament at Fia's Lounge, Bangalore, 11 May 2026.**

## What's here

```
mothers-day-mahjong/
├── assets/
│   └── logo_mahjong_fias.png         brand watermark used in the reel
├── metadata/
│   ├── inventory.csv                 65 .MOV + 22 .JPG — codecs, duration, resolution, fps
│   ├── classification.csv            vision-tagged: food / mahjong / people / mixed / unclear
│   ├── exclude.txt                   11 food clips dropped from picker pool
│   ├── beat_grid.json                Cherry Cherry Lady — BPM 112.35, downbeats, 30s window
│   ├── analyze.py                    librosa script that produced beat_grid.json
│   ├── edit_notes.md                 BPM cheat sheet (beat duration, cut intervals)
│   └── shakiness_scores.csv          vidstabdetect per-slot scores (used in v7→v8 drop)
└── shotlists/
    ├── shotlist_v1.csv               first cut — 33 slots, 30s
    ├── shotlist_v2.csv               Fia opener + 2 shaky swaps
    ├── shotlist_v3.csv               logo overlay added
    ├── shotlist_v4.csv               brand-card src_in tuning
    ├── shotlist_v6.csv               NVENC GOP drift bug fixed
    ├── shotlist_v7.csv               placard + wide-table opening
    ├── shotlist_v8.csv               auto-drop 4 shaky clips (vidstab)
    └── shotlist_v9_final.csv         no static JPGs — 25.6s production cut
```

## What you'd need to actually re-render this reel

The repo intentionally excludes the heavy/private/copyright assets. To re-run:

| File | Where to source |
|---|---|
| 65 `IMG_*.MOV` source clips | The iPhone footage from the event (private — not in repo) |
| 22 `IMG_*.JPG` photos | Same shoot |
| `cherry_lady_30s_faded.wav` | Run `metadata/analyze.py` on Cherry Cherry Lady audio (yt-dlp from official Modern Talking YouTube) |

The pipeline scripts (`../../pipeline/`) are repo-included — they reconstruct everything else (shotlist.csv, render_reel.sh, resolve_import.py) from the SHOTS list in `build_shotlist.py`.

## Brand assets disclaimer

`assets/logo_mahjong_fias.png` is the **Mahjong @ Fia's Lounge** brand mark. It's included here as the original commissioning event's identity. Substitute your own logo before adapting this pipeline for other projects.
