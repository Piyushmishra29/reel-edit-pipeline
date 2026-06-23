# Fia's Tiles Reel — Edit Notes (match-cut "appear" reel)

Recreation of the reference `Video-533.mp4`: a **match-cut reel** where a mahjong
tile *materializes* in a fixed frame. On each cut the location/look changes while
an **anchor stays locked in place**, so the tile appears to pop into existence.
Audio is the borrowed sound from the reference (gitignored), footage audio muted.

## The mechanic (what makes a reveal "land")

A reveal is a hard cut between an **empty** state and a **tile-present** state,
where the anchor is in the **identical position and motionless** before and after.
The eye locks on the still anchor, so only the tile changes → it materializes.

If the anchor (hand/tile) is **moving** across the cut, it reads as a jump, not an
appear. This is the single thing that makes or breaks every reveal.

## Shipped cut — 2 reveals (both verified clean)

| Reveal | Location | Empty → Tile | Anchor | Source |
|--------|----------|--------------|--------|--------|
| 1 | restaurant window | empty pinch → tile in pinch | hand | IMG_4657 (0.95s→3.15s) |
| 2 | mural | empty dragon table → tiles on table | table | IMG_4677 (1.50s→4.30s) |

Then the full-table beat holds ~0.6s and the music fades. Output: 720×1280, 30fps,
~3.8s. EDL in `shotlists/shotlist_matchcut_2reveal.csv`; build with
`build_matchcut_reel.sh`.

## Why reveal 3 was cut (footage limitation, not editing)

Three different clips were shot/tried for a 3rd reveal — IMG_4671 (standing),
IMG_4666 and IMG_4667 (carved wall). **None works**, for the same reason, proven
frame-by-frame:

- In all three, her **hand is in motion** during the empty state — reaching,
  rising, pointing — and she's **already holding the tile** by the time her hand is
  presentable. There is no moment where an empty hand and a tile-in-hand sit
  **still in the same spot**.
- Reveal 1 works precisely because in IMG_4657 her pinch is **motionless** at
  chest-center, empty then with the tile.
- Reframing can move position but cannot freeze a moving hand or turn an open/
  pointing gesture into a matching pinch — so the appear can't be faked in the edit.

### Reshoot recipe for a clean reveal 3
1. Phone on a tripod / propped — **locked, not handheld**.
2. Hold an **empty pinch** (thumb + finger) **completely still** at chest center ~2s.
3. Without moving the hand, place the tile into that **same pinch**; hold ~2s.
4. Same framing/outfit, hand never moves → it match-cuts as cleanly as reveal 1.

## Per-segment encode

Each segment: trim from `src_in`, `scale=720:1280:force_original_aspect_ratio=
increase,crop=720:1280` + `fps=30`. Source clips are 9:16 already so the crop is a
no-op; iPhone −90 rotation is auto-applied on decode. Slots driven by exact
`-frames:v` counts (no fps-rounding drift). CPU `libx264 -crf 18` locally;
`USE_NVENC=1` for the RTX box. Footage audio dropped (`-an`); only the borrowed
template audio is muxed, with a 0.5s fade-out.
