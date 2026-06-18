# Fia's Tiles Reel — Edit Notes

Exact remake of the reference clip `Video-533.mp4` (a vertical trend template).
The reference clip *is* the beat grid, so no librosa/BPM pass — cut points come
straight from the reference's scene cuts.

## Template (from Video-533.mp4)

- 720×1280, 30 fps, 4 hard-cut slots (subject changes pose/location at each cut —
  verified by frame inspection, it's a genuine 4-shot transition template).
- Scene cuts detected with `ffmpeg select='gt(scene,0.3)'`: 2.033 / 3.967 / 5.633 s.
- Boundaries snapped to exact 30 fps frames so cuts land with zero drift:
  frame 0 / 61 / 119 / 169.

| Slot | Start frame | Frames | Start–End (s)   |
|------|-------------|--------|-----------------|
| 1    | 0           | 61     | 0.000 – 2.033   |
| 2    | 61          | 58     | 2.033 – 3.967   |
| 3    | 119         | 50     | 3.967 – 5.633   |
| 4    | 169         | 60     | 5.633 – 7.633   |

Total **229 frames = 7.633 s**.

### Duration facts (audited)

- Reference **video** stream: 7.600 s / 228 frames.
- Reference **audio**: container reports 7.729 s, but ~0.088 s of that is AAC
  priming trimmed on decode — real decodable audio is **7.641 s**.
- So slot 4 is sized to the audio (60 frames, ending 7.633 s) rather than the
  reference video's 228th frame. Output: video 7.633 s, audio 7.641 s.

Audio: extracted verbatim from the reference (`metadata/extract_audio.sh`),
loudness as-is, 7.641 s. Borrowed sound — gitignored.

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

Each clip trimmed from `src_in` 0.5 s (skips the grab), then
`scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280` + `fps=30`.
Source clips are 9:16 already, so the crop is a no-op — no content lost.
iPhone clips carry −90 rotation which ffmpeg auto-applies on decode, so no manual
transpose. CPU `libx264 -crf 18` locally; `USE_NVENC=1` for the RTX box.

Two gotchas found during audit and fixed:
- **Slots are sized by `-frames:v` (exact frame counts), not float `-t` seconds.**
  Float durations + the `fps` filter round each slot down, drifting the cuts off
  the grid (first build was 226 frames / 7.53 s instead of 229).
- **No `-shortest` on the final mux.** With AAC audio, `-shortest` stops the mux
  early on a priming-padding boundary and truncated the video to 7.53 s. Dropping
  it gives the full 229-frame video.
