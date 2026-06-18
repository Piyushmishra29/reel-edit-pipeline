#!/usr/bin/env bash
# Extract the borrowed soundtrack from the reference template clip.
# The reference clip + extracted audio are private/borrowed assets (gitignored).
set -euo pipefail

REF="${1:-$HOME/Downloads/Video-533.mp4}"
OUT="$(dirname "$0")/../assets/template_audio.wav"

ffmpeg -y -hide_banner -loglevel error -i "$REF" -vn -acodec pcm_s16le -ar 48000 "$OUT"
echo "Wrote $OUT"
