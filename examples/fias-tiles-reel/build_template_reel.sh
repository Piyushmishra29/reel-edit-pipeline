#!/usr/bin/env bash
# Build the Fia's tiles reel as an exact remake of Video-533.mp4's 4-slot template.
#
# Reads shotlists/shotlist_template_v1.csv -> trims each chosen clip to its slot,
# scales/crops to 720x1280@30, concatenates, muxes the borrowed template audio.
#
# Source footage + audio are private/borrowed (gitignored). Override paths via env:
#   SRC_DIR   folder holding the IMG_*.MOV clips
#   AUDIO     extracted template audio wav
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="${SRC_DIR:-$HOME/Downloads/Tiles reel June 26 }"
AUDIO="${AUDIO:-$HERE/assets/template_audio.wav}"
SHOTLIST="${SHOTLIST:-$HERE/shotlists/shotlist_template_v1.csv}"
OUT="${OUT:-$HERE/reel_v1.mp4}"
W=720; H=1280; FPS=30

# Encoder: CPU x264 locally; flip USE_NVENC=1 on the RTX box for the fast path.
if [ "${USE_NVENC:-0}" = "1" ]; then
  VENC=(-c:v h264_nvenc -preset p5 -b:v 8M)
else
  VENC=(-c:v libx264 -preset medium -crf 18)
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CONCAT="$TMP/concat.txt"; : > "$CONCAT"

echo "=== Building slots ==="
# Skip CSV header, read each slot row.
tail -n +2 "$SHOTLIST" | while IFS=, read -r slot file src_in tl_len motion label; do
  [ -z "${slot:-}" ] && continue
  in_clip="$SRC_DIR/$file"
  out_slot="$TMP/slot_$(printf '%02d' "$slot").mp4"
  echo "  slot $slot: $file  in=$src_in len=$tl_len  ($label)"
  ffmpeg -nostdin -y -hide_banner -loglevel error \
    -ss "$src_in" -t "$tl_len" -i "$in_clip" \
    -vf "scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},setsar=1,fps=${FPS}" \
    -an "${VENC[@]}" -pix_fmt yuv420p -video_track_timescale 30000 "$out_slot"
  echo "file '$out_slot'" >> "$CONCAT"
done

echo "=== Concatenating + muxing audio ==="
ffmpeg -y -hide_banner -loglevel error \
  -f concat -safe 0 -i "$CONCAT" \
  -i "$AUDIO" \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k -shortest \
  "$OUT"

echo "=== Done: $OUT ==="
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,width,height,r_frame_rate -of default=noprint_wrappers=1 "$OUT"
