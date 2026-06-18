# Fia's Tiles Reel — Edit Notes

Exact remake of the reference clip `Video-533.mp4` (a vertical trend template).
The reference clip *is* the beat grid, so no librosa/BPM pass — cut points come
straight from the reference's scene cuts.

## Template (from Video-533.mp4)

- 720×1280, 30 fps, 7.729 s, 4 hard-cut slots.
- Scene cuts detected with `ffmpeg select='gt(scene,0.3)'`: 2.033 / 3.967 / 5.633 s.

| Slot | Start | End   | Duration |
|------|-------|-------|----------|
| 1    | 0.000 | 2.033 | 2.033    |
| 2    | 2.033 | 3.967 | 1.934    |
| 3    | 3.967 | 5.633 | 1.666    |
| 4    | 5.633 | 7.729 | 2.096    |

Audio: extracted verbatim from the reference (`metadata/extract_audio.sh`),
loudness as-is, ~7.64 s. Borrowed sound — gitignored.

## Clip selection — 8 candidates, 4 slots

vidstabdetect was unavailable locally (brew ffmpeg 8.1 built without libvidstab),
so steadiness was ranked with a **frame-difference motion proxy**: mean luma of
`tblend=difference` frames over a 2.1 s window at 480p. Lower = steadier.

| Clip         | Motion | Picked |
|--------------|--------|--------|
| IMG_4648.MOV | 3.206  | ✅ slot 1 |
| IMG_4657.MOV | 3.233  | ✅ slot 2 |
| IMG_4677.MOV | 3.343  | ✅ slot 3 |
| IMG_4637.MOV | 3.545  | ✅ slot 4 |
| IMG_4651.MOV | 3.613  | — |
| IMG_4652.MOV | 3.618  | — |
| IMG_4639.MOV | 4.300  | — |
| IMG_4671.MOV | 10.420 | ❌ clearly shaky |

Scores in `metadata/motion_scores.csv`. Slot order = steadiness order; reorder
in `shotlists/shotlist_template_v1.csv` to taste.

## Per-slot encode

Each clip trimmed from `src_in` 0.5 s (skips the grab) for the slot duration,
then `scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280` +
`fps=30`. iPhone clips carry −90 rotation which ffmpeg auto-applies on decode, so
no manual transpose. CPU `libx264 -crf 18` locally; `USE_NVENC=1` for the RTX box.
