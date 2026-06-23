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

## Shipped cut — 3 reveals (all verified clean)

| Reveal | Location | Empty → Tile | Anchor | Source |
|--------|----------|--------------|--------|--------|
| 1 | restaurant window | empty pinch → tile in pinch | hand | IMG_4657 (0.95s→3.15s) |
| 2 | mural | empty dragon table → tiles on table | table | IMG_4677 (1.50s→4.30s) |
| 3 | carved wall | empty extended pinch → tile in pinch | hand | IMG_4871 (3.00s→3.60s) |

Then the full-table beat holds ~0.6s and the music fades. Output: 720×1280, 30fps,
~5.2s (156 frames). EDL in `shotlists/shotlist_matchcut_3reveal.csv`; build with
`build_matchcut_reel.sh`.

## Reveal 3 — what made the reshoot land

Earlier reveal-3 attempts all failed for one reason, proven frame-by-frame: the
hand was **in motion** during the empty state (reaching, rising, pointing) and she
was **already holding the tile** by the time the hand was presentable — so there
was never a moment where an empty hand and a tile-in-hand sat **still in the same
spot**. Tried and rejected: IMG_4671 (standing), IMG_4666, IMG_4667 (carved wall).

The locked reshoot **IMG_4871.MOV** fixes it. She holds an **empty extended pinch
still** (~3.00–3.50s), then the tile **materializes in that same pinch** at ~3.57s
and is held steady (~3.60–4.35s). The hand does not move across the cut, so it
reads as an appear — exactly like reveal 1. The cut sits at output frame 112
(3.733s): empty hand → tile-in-hand, identical position.

### Reshoot recipe that worked (keep for any future reveal)
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
