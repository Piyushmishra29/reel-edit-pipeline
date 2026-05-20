# Fia's Mahjong Collection — VO-driven product launch reel

<p align="center"><i>A 24-second vertical reel announcing the new Mahjong @ Fia's Lounge collection — premium tiles, velvet mats, smooth pushers, and beautifully crafted racks.</i></p>

<p align="center">
  <img alt="format" src="https://img.shields.io/badge/format-1080×1920-blue"/>
  <img alt="duration" src="https://img.shields.io/badge/duration-24.23s-green"/>
  <img alt="engine" src="https://img.shields.io/badge/engine-VO--driven-orange"/>
  <img alt="renderer" src="https://img.shields.io/badge/renderer-h264__videotoolbox-success"/>
</p>

---

## What this is

A product-launch reel for **Mahjong @ Fia's Lounge** built end-to-end on a MacBook with `ffmpeg` (VideoToolbox), `whisper-cpp`, `playwright`, and `imagemagick`. The host narrates a five-sentence script; visuals cut to her words, not to a music beat. Output ships at Instagram-spec loudness and aspect ratio.

The final caption track:

> The most beautiful Mahjong setup is here. ✨🀄️
> Introducing our newest collection at Fia's Lounge —
> premium Mahjong tiles, smooth pushers, luxurious velvet mats, and beautifully crafted Mahjong racks.
> Designed to bring elegance, comfort, and style to every game.
> Visit our website to explore the full collection.

---

## How it was built

The full v1 → v9 case study — every defect, every fix, the audio-mix architecture, and the data model — lives in [`examples/fias-mahjong-collection/ITERATION_LOG.md`](examples/fias-mahjong-collection/ITERATION_LOG.md). The short version:

```
01-source/IMG_xxxx.MOV ── ffprobe ─► inventory.csv
                       ── midpoint thumbs ─► 02-thumbs/
                       ── manual vision pass ─► classification.csv (host / racks / mats / tiles / setup / detail)

host clips ──► silencedetect @ -45dB ──► clean speech ranges (VO[])
            ── whisper-cpp medium.en  ──► transcription mapping (which clip is which sentence)

scripts/capture_site.js (Playwright + Chromium) ──► assets/site_mahjongatfias.png  (1080×7830 long screenshot)

03-music/bed.wav ── yt-dlp -4 + ffmpeg trim/fade ──► music bed

scripts/build_reel.py
  ├─ VO[]      : sentence + src range + breathing gap
  ├─ CUTS[]    : visual slots anchored to VO segments
  ├─ CAPTIONS[]: per-role on-screen text (currently empty for v9)
  └─ Renders   :
        Pass 1  per-slot 1080×1920 silent MP4 (h264_videotoolbox)
        Pass 1b extract each VO segment + apad gap, concat → vo_concat.wav
        Pass 2  concat slots, build audio mix, mux, loudnorm → reel_vN.mp4
```

### Audio architecture

Voice is the loudest element by design. Music sits underneath, ducked further when she speaks.

```
[bed] = music   ── highpass 250 Hz ── volume 0.07
[vo]  = VO concat ── asplit ──┬── [vo_sc] (triggers ducking)
                              └── [vo_mix] (mixed back at 8:1)

[bed][vo_sc]    sidechaincompress(threshold 0.02, ratio 20, attack 2, release 350)  → [ducked]
[ducked][vo_mix] amix(weights "1 8", duration=first, normalize=0)                   → [mix1]
[mix1]           loudnorm(I=-16, LRA=11, TP=-1.5)                                   → [mix]
```

The 8:1 mix ratio is the safety net; the sidechain compressor is the polish. If sidechain ducking ever silently fails, voice still wins.

---

## Working with this branch

Every file in `examples/fias-mahjong-collection/` belongs to this project:

| File | What it is |
|---|---|
| [`README.md`](examples/fias-mahjong-collection/README.md) | End-to-end 7-step recipe (ingest, transcribe, capture site, music, edit, render) |
| [`ITERATION_LOG.md`](examples/fias-mahjong-collection/ITERATION_LOG.md) | Detailed case study of every render iteration v1→v9 |
| [`scripts/build_reel.py`](examples/fias-mahjong-collection/scripts/build_reel.py) | The engine — VO + CUTS + CAPTIONS → shotlist + render_reel.sh |
| [`scripts/capture_site.js`](examples/fias-mahjong-collection/scripts/capture_site.js) | Playwright long-page screenshot of `mahjongatfias.in` |
| [`metadata/inventory.csv`](examples/fias-mahjong-collection/metadata/inventory.csv) | Per-clip duration / codec / resolution from this shoot |
| [`metadata/classification.csv`](examples/fias-mahjong-collection/metadata/classification.csv) | Manual vision tagging for 34 clips |
| [`metadata/shotlist_v9.csv`](examples/fias-mahjong-collection/metadata/shotlist_v9.csv) | Final timeline locked for v9 |
| [`metadata/shotlist_v9.md`](examples/fias-mahjong-collection/metadata/shotlist_v9.md) | Human-readable timeline + VO bed table |
| [`assets/site_mahjongatfias.png`](examples/fias-mahjong-collection/assets/site_mahjongatfias.png) | 1080×7830 long screenshot for the CTA scroll |

Footage, rendered MP4s, the music bed, and intermediate slot files are all `.gitignore`d (private + copyrighted material).

---

## Reproducing the render

Assuming you have access to the raw footage and a Mac with the dependencies installed:

```bash
# Project root assumed at ~/Desktop/fias-mahjong-collection
cd ~/Desktop/fias-mahjong-collection

# 1. Inventory + thumbnails + manual classification (one-time)
#    See examples/fias-mahjong-collection/README.md steps 2-3.

# 2. Transcribe the host clips, pick speech ranges (one-time)
#    See README step 4. Update VO[] in scripts/build_reel.py.

# 3. Capture the CTA site (re-run only if the site changes)
node scripts/capture_site.js

# 4. Music bed (re-run only if the track changes)
yt-dlp -4 -x --audio-format wav -o "03-music/bed_source.%(ext)s" "ytsearch1:Neiked Following the Sun"
ffmpeg -y -ss 0 -t 22.63 -i 03-music/bed_source.wav \
       -af "afade=t=in:d=0.8,afade=t=out:st=21.13:d=1.5" 03-music/bed.wav

# 5. Render
python3 scripts/build_reel.py
bash 04-edit/render_reel.sh
open 05-renders/reel_v9.mp4
```

The script will fail loudly if any visual slot wants more footage than its source clip has — that sanity check was added in v2 after slot 7 silently truncated by 1 full second in v1.

---

## Skills used

| Layer | Tech | Why |
|---|---|---|
| Decode/encode | `ffmpeg 8.1` + `h264_videotoolbox` | Hardware H.264 on Mac without NVIDIA |
| Speech-range detection | `ffmpeg silencedetect` @ -45dB / 0.25s | Find clean takes inside each host clip |
| Transcription | `whisper-cpp` medium.en | Map each take to its caption-script line |
| Vertical reframe | `crop=ih*9/16:ih,scale=1080:1920` | 1080×1920 from 4K HEVC iPhone sources |
| Frame-exact slots | `-frames:v N` (instead of `-t`) | Avoids drift across many slots; inventory sanity check catches truncation |
| Caption rendering | ImageMagick PNG → ffmpeg `overlay` | Mac ffmpeg from Homebrew lacks libfreetype, so no `drawtext` |
| CTA site capture | Playwright + Chromium, 540×960 / 2× DPR | Mobile-shaped long screenshot for vertical scroll |
| Animated scroll | ffmpeg `crop` with time-varying `y` expression | Top-to-bottom scroll over the CTA window |
| Music download | `yt-dlp -4` | YouTube search API requires IPv4 |
| Audio normalization | `ffmpeg loudnorm` (EBU R128) | -16 LUFS for Instagram/TikTok |
| Audio ducking | `asplit` + `sidechaincompress` + `amix weights="1 8"` | Voice dominant, music ducked under |
| Container | MP4 + `+faststart` moov atom | Progressive web playback |

---

## Iteration timeline

| v | Duration | Headline |
|---|---|---|
| v1 | 17.73s | Two phrases silently missing from VO; CTA visual truncated 1s |
| v2 | 22.63s | Full VO restored, CTA clip swapped, inventory sanity check added |
| v3 | 22.63s | Captions + animated website scroll + music bed |
| v4 | 22.63s | Music down to `0.06`, HPF, harder sidechain |
| v5 | 22.63s | Captions on, CTA split — **VO inaudible** (sidechain consumed it) |
| v6 | 22.63s | Audio mix rebuilt with `asplit`; captions removed |
| v7 | 24.23s | 0.4s breath after each sentence; reveal swap; hook visual on IMG_3794 |
| v8 | 24.23s | Hook audio also from IMG_3794 (src_in 1.78) — lip-synced |
| v9 | 24.23s | Music `0.05 → 0.07` — **locked** |

Full play-by-play in [`ITERATION_LOG.md`](examples/fias-mahjong-collection/ITERATION_LOG.md).

---

## Credits

Reel built for **Fia's Lounge** (Bengaluru), the new Mahjong collection store at `mahjongatfias.in`.

Assembled with [Claude Code](https://claude.com/claude-code) (Opus 4.7, 1M context).

## License

MIT — see [LICENSE](LICENSE)
