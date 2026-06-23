#!/usr/bin/env bash
# Build the Fia's tiles MATCH-CUT reel: each reveal is an "appear" cut anchored on
# a fixed element (the tile materializes while the anchor stays put), in the spirit
# of the reference Video-533.mp4.
#
# Shipped cut = 2 reveals (both verified clean):
#   R1  restaurant : empty pinch -> tile in pinch        (anchor = hand)
#   R2  mural      : empty dragon table -> tiles on table (anchor = table)
#   then hold the full-table beat, music fades.
#
# Edit decision list: shotlists/shotlist_matchcut_2reveal.csv
# Source footage + borrowed audio are private/gitignored. Override with env:
#   SRC_DIR  folder with the IMG_*.MOV clips   AUDIO  extracted template audio
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="${SRC_DIR:-$HOME/Downloads/Tiles reel June 26 }"
AUDIO="${AUDIO:-$HERE/assets/template_audio.wav}"
OUT="${OUT:-$HERE/reel_2reveal_final.mp4}"
W=720; H=1280; FPS=30
VF="scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},setsar=1,fps=${FPS}"
if [ "${USE_NVENC:-0}" = "1" ]; then VENC=(-c:v h264_nvenc -preset p5 -b:v 8M); else VENC=(-c:v libx264 -preset medium -crf 18); fi

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
seg(){ # file src_in frames out
  ffmpeg -nostdin -y -hide_banner -loglevel error -ss "$2" -i "$SRC_DIR/$1" \
    -vf "$VF" -frames:v "$3" -an "${VENC[@]}" -pix_fmt yuv420p -video_track_timescale 30000 "$4"; }

echo "=== reveal segments (empty -> tile, hard match cuts) ==="
seg IMG_4657.MOV 0.95 22 "$TMP/1a.mp4"   # R1 empty pinch
seg IMG_4657.MOV 3.15 26 "$TMP/1b.mp4"   # R1 tile appears in pinch
seg IMG_4677.MOV 1.50 22 "$TMP/2a.mp4"   # R2 empty dragon table
seg IMG_4677.MOV 4.30 26 "$TMP/2b.mp4"   # R2 tiles appear on table
for s in 1a 1b 2a 2b; do echo "file '$TMP/$s.mp4'"; done > "$TMP/c.txt"
ffmpeg -nostdin -y -hide_banner -loglevel error -f concat -safe 0 -i "$TMP/c.txt" -c:v copy "$TMP/cat.mp4"

echo "=== hold final beat 0.6s + mux music (fade out) ==="
ffmpeg -nostdin -y -hide_banner -loglevel error -i "$TMP/cat.mp4" \
  -vf "tpad=stop_mode=clone:stop_duration=0.6" "${VENC[@]}" -pix_fmt yuv420p -video_track_timescale 30000 "$TMP/vid.mp4"
TOT=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/vid.mp4")
ffmpeg -nostdin -y -hide_banner -loglevel error -i "$TMP/vid.mp4" -i "$AUDIO" \
  -map 0:v:0 -map 1:a:0 -c:v copy -af "afade=t=out:st=$(python3 -c "print(round($TOT-0.5,3))"):d=0.5" \
  -c:a aac -b:a 192k -t "$TOT" "$OUT"
echo "=== done: $OUT ==="
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,width,height,r_frame_rate -of default=noprint_wrappers=1 "$OUT"
