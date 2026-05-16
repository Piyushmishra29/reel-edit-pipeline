# Cherry Cherry Lady - Editor Cheat Sheet

Source: Modern Talking - Cheri Cheri Lady (Official Video, Modern Talking Offiziell)
YouTube: https://www.youtube.com/watch?v=eNvUS-6PTbs  (3:17, ~928M views)

## Tempo

- **Detected BPM: 112.35**
- **Beat interval: 0.5341 s** (= 60 / 112.35)
- Bar length (4/4): 2.136 s

## Cut-cadence suggestions

The brief asked for 1 s / 0.5 s / 0.25 s cuts. At 112 BPM those map to:

| Target cut | Beats     | Snapped duration |
| ---------- | --------- | ---------------- |
| ~1.00 s    | every 2   | 1.068 s          |
| ~0.50 s    | every 1   | 0.534 s          |
| ~0.25 s    | every 1/2 | 0.267 s          |

Editor tip: 4 cuts per bar (every beat, 0.534 s) is the safest groove sit.
For accents, hit every 2nd beat (the "downbeat / snare" pulse, 1.068 s).
For rapid mahjong-tile flurries, go half-beat (0.267 s) inside a single bar then
release on the next downbeat.

## 30-second window choice

- **Original-song range: 42.54 s -> 72.49 s** (~00:42 - 01:12)
- This sits in the **first chorus into the post-chorus / verse-2 transition**.
  Musically: the hook "Cheri Cheri Lady, going through a motion..."
  lands inside this window, with the sustained synth pad + drum machine
  groove that defines the track.
- The loudest RMS peak in the whole song is at **161.1 s** (final chorus),
  but the early-chorus window was chosen for reel cold-open energy and to
  avoid starting on a fade.
- Window is snapped to nearest beat at both ends; duration = 29.954 s
  (58 beats inside).

## First 10 downbeats inside the 30 s window

(Use these as clip-marker positions in the NLE.)

| # | Window-relative (s) | Original-song (s) |
|---|---------------------|-------------------|
| 1 | 0.000               | 42.539            |
| 2 | 2.113               | 44.652            |
| 3 | 4.226               | 46.765            |
| 4 | 6.316               | 48.855            |
| 5 | 8.406               | 50.945            |
| 6 | 10.519              | 53.058            |
| 7 | 12.632              | 55.171            |
| 8 | 14.722              | 57.261            |
| 9 | 16.834              | 59.373            |
| 10| 18.924              | 61.463            |

Full per-beat grid (all 58 beats, plus onset peaks) is in `beat_grid.json`.

## Files

- `cherry_lady_full.wav` - original 3:17 download, 48 kHz stereo PCM
- `cherry_lady_30s.wav` - clean 29.954 s cut, 48 kHz stereo PCM
- `cherry_lady_30s_faded.wav` - same window, 0.05 s fade-in + 0.5 s fade-out,
  loudness-normalized to **-16 LUFS / -1.5 dB TP / LRA 11** (Instagram spec)
- `beat_grid.json` - full beat / onset / window metadata
- `analyze.py` - reproducible analysis script
