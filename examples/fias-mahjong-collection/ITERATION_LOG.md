# Iteration log — Fia's Mahjong Collection reel

A blow-by-blow of how this reel went from a broken first render to a locked v9. Useful both as a debugging case study and as a recipe for the next reel.

The headline data:

| v | Duration | What landed | What broke |
|---|---|---|---|
| v1 | 17.73s | First end-to-end render | Two phrases missing entirely from VO; CTA visual silently truncated 1s |
| v2 | 22.63s | Full VO restored, CTA visual swapped, sanity check added | None — audio narrative intact |
| v3 | 22.63s | Per-section captions, animated `mahjongatfias.in` scroll over CTA, music bed (Neiked – Following the Sun) | Music too present under VO |
| v4 | 22.63s | Music volume `0.18 → 0.06`, HPF 200 Hz, sidechain ratio 8 → 20, VO gain `1.0 → 1.2` | Music still audible during VO |
| v5 | 22.63s | Music `0.03`, HPF 250 Hz, VO `1.3`, CTA split (1.90s pagoda + 1.63s scroll) | **VO inaudible** — sidechain compressor consumed the VO as trigger, never mixed it back |
| v6 | 22.63s | Audio mix rebuilt with `asplit`; captions removed; `WEBSITE_SCROLL` filter chain fixed for no-caption case | None — VO present and dominant |
| v7 | 24.23s | 0.4s breath after each sentence; reveal swap from IMG_3820 (too short for breath) to IMG_3824; hook visual swap to IMG_3794 | Audio still pulled from IMG_3795 → lips out of sync |
| v8 | 24.23s | Hook audio _and_ visual on IMG_3794 src 1.78s (slate skipped, lip-synced) | Music slightly too quiet now |
| v9 | 24.23s | Music `0.05 → 0.07` | Locked |

---

## v1 → v2 — Two phrases were missing from the VO

### Symptom

Watching v1, the user reported "video cuts early, voice is getting cut, whole message isn't getting through."

### Root cause

`silencedetect` was running with `noise=-30dB:duration=0.3` to find clean takes inside each host clip. That threshold is too aggressive — quiet trailing word releases and mid-sentence breaths register as silence, so the VO ranges trimmed off real speech.

Re-running at `-45dB / 0.25s` exposed the loss:

| VO line | v1 range | True range (-45dB) | Loss |
|---|---|---|---|
| hook | 5.98 → 8.46 (2.48s) | 5.97 → 9.23 (3.26s) | -0.77s |
| reveal | 0.94 → 3.26 (2.32s) | 0.93 → 3.36 (2.43s) | -0.11s |
| products | 3.36 → 10.42 (7.06s) | 3.35 → 10.97 (7.62s) | -0.55s |
| **value** | **1.62 → 4.57 (2.95s)** | **1.43 → 5.72 (4.29s)** | **-1.34s — "in every game" cut entirely** |
| **cta** | **2.38 → 4.80 (2.42s)** | **0.96 → 4.49 (3.53s)** | **-1.11s — "Visit our website" cut entirely** |

Two whole phrases were missing from v1. The VO sounded like:

> "Designed to bring elegance, style and comfort." ❌ no "in every game"
> "explore the full collection." ❌ no "Visit our website to"

### Second bug, same render

Slot 7 (CTA visual) requested 2.42s from `IMG_3823.MOV`. The source clip is 1.435s long. `ffmpeg -frames:v 73` silently capped at 43 frames. Final reel duration dropped from a planned 18.73s to 17.73s and the audio/visual fell out of sync at the end.

### Fix

1. **Re-trim every VO range at -45dB / 0.25s** and re-pick the longest continuous speech burst in each clip.
2. **Swap the CTA source** from IMG_3823 (1.4s) to IMG_3824 (7.2s).
3. **Add a sanity check** at the top of the render pipeline that reads `inventory.csv` and asserts every slot fits inside its source. This catches the `-frames:v N` truncation bug at build time instead of at render time.

```python
SRC_DUR = {row["filename"]: float(row["duration_sec"])
           for row in csv.DictReader(open(SRC/"inventory.csv"))}
for s in slots:
    if s["file"] in ("LOGO_END_CARD", "WEBSITE_SCROLL"):
        continue
    avail = SRC_DUR[s["file"]] - s["src_in"]
    assert avail >= s["dur"] - 0.05, (
        f"slot {s['role']}: needs {s['dur']:.2f}s from {s['file']} at "
        f"src_in={s['src_in']:.2f}, only {avail:.2f}s available"
    )
```

---

## v2 → v3 — Captions, website scroll, music bed

The reel was telling the right story but viewers needed visual reinforcement of the spoken script and a clearer CTA. Three additions:

### Captions (one PNG per role)

The Mac `ffmpeg 8.1` built via Homebrew **does not include `libfreetype`**, so the `drawtext` filter is unavailable. Switched to ImageMagick → PNG → ffmpeg `overlay`:

```python
def build_caption_pngs():
    for role, text in CAPTIONS.items():
        if not text: continue
        h = 130 if "\n" not in text else 220
        subprocess.run([
            "magick",
            "-background", "rgba(0,0,0,0.6)",
            "-fill", "white",
            "-font", FONT_PATH,
            "-pointsize", "56",
            "-gravity", "center",
            "-interline-spacing", "16",
            "-size", f"1080x{h}",
            f"caption:{text}",
            f"PNG32:{out}",
        ], check=True)
```

Each slot's render uses a `-filter_complex` instead of `-vf` so it can take a second input (the caption PNG):

```
[0:v]crop=ih*9/16:ih,scale=1080:1920,fps=30[bg];
[bg][1:v]overlay=0:CAPTION_Y:format=auto,format=yuv420p[v]
```

### Animated website scroll over CTA

Captured `mahjongatfias.in` as a long 1080×7830 PNG via Playwright + Chromium (`scripts/capture_site.js`). Then animated a crop window scrolling top-to-bottom over the slot duration:

```bash
ffmpeg -loop 1 -t DUR -i SITE \
  -vf "scale=1080:-2,
       crop=w=1080:h=1920:x=0:y='min((ih-1920)*t/DUR,(ih-1920))':exact=1,
       fps=30"
```

A new sentinel `WEBSITE_SCROLL` in CUTS (alongside `LOGO_END_CARD`) routes to this filter chain.

### Network gotcha

`yt-dlp` over IPv6 routinely fails the YouTube search API with `Errno 65: No route to host`. Forcing IPv4 fixes it:

```bash
yt-dlp -4 --no-playlist -x --audio-format wav "ytsearch1:<artist> <track>"
```

### Music bed integration

Trim to exact reel duration with fades, then mux as a third audio input under the VO:

```bash
ffmpeg -ss 0 -t 22.63 -i bed_source.wav \
  -af "afade=t=in:d=0.8,afade=t=out:st=21.13:d=1.5" \
  03-music/bed.wav
```

---

## v3 → v4 → v5 — The music problem

User feedback after each iteration tightened the mix:

| | v3 | v4 | v5 |
|---|---|---|---|
| `volume` (music) | 0.18 | 0.06 | 0.03 |
| HPF cutoff | none | 200 Hz | 250 Hz |
| VO gain | 1.0 | 1.2 | 1.3 |
| `sidechain ratio` | 8 | 20 | 20 (max) |
| `sidechain threshold` | 0.05 | 0.02 | 0.015 |
| `attack`/`release` | 5/200 | 2/300 | 2/350 |

The high-pass on the music bed removes the bass that competes with the voice register; sidechain compression ducks the music when the voice triggers.

### v5: VO disappeared entirely

This is the most expensive bug of the project. v5's filter graph was:

```
[bed][vo]sidechaincompress=...[mix1]
[mix1]loudnorm=...[mix]
```

`sidechaincompress` is a two-input filter:
- **Main** (first input) — the signal that gets compressed
- **Sidechain trigger** (second input) — drives the compressor's gain reduction; **not passed to the output**

So `[mix1]` is _only the ducked music_. The VO was consumed as a trigger and never reached the mux. The user heard quiet music and zero voice.

---

## v5 → v6 — Audio mix rebuilt with `asplit`

Fix the consumption problem by duplicating the VO before it enters the compressor:

```
[2:a] aloop, atrim, highpass=f=250, volume=0.05 → [bed]
[1:a] volume=1.0 → [vo]
[vo]  asplit=2 → [vo_mix] + [vo_sc]
[bed][vo_sc] sidechaincompress(threshold=0.02, ratio=20, attack=2, release=350) → [ducked]
[ducked][vo_mix] amix=inputs=2:duration=first:weights=1 8:normalize=0 → [mix1]
[mix1] loudnorm=I=-16:LRA=11:TP=-1.5 → [mix]   # Instagram spec
```

Two things matter here:

1. **`asplit=2[vo_mix][vo_sc]`** — one copy of the VO triggers ducking, the other survives to be mixed in.
2. **`amix=weights=1 8`** — VO is mixed eight times louder than the ducked music. The weights are the safety net; the sidechain ducking is polish on top. If sidechain were ever to fail silently, the 8:1 ratio still keeps the voice loud.

`normalize=0` disables amix's automatic normalization, which otherwise would attenuate both inputs to fit the sum into 0 dB. We've already targeted -16 LUFS via `loudnorm`.

Also in v6:
- Captions disabled (`CAPTIONS[*] = None`) per user feedback.
- The `WEBSITE_SCROLL` filter chain had a bug when no caption was present — the chain ended with `[bg]` (a label), and then we appended `,format=yuv420p[v]` to it, which is illegal. Fixed by terminating the chain only when the overlay is needed.

---

## v6 → v7 → v8 — Natural pauses + lip-synced hook

User: "make the video a little slower, the VO doesn't have a break, make it natural sounding."

### `gap_after` per VO segment

Extended the VO tuple from 5 to 6 fields:

```python
VO = [
    ("IMG_3794.MOV", 1.78, 5.05,  "hook",     "...", 0.40),   # +0.4s breath
    ("IMG_3797.MOV", 0.93, 3.36,  "reveal",   "...", 0.40),
    ("IMG_3800.MOV", 3.35, 10.97, "products", "...", 0.40),
    ("IMG_3804.MOV", 1.43, 5.72,  "value",    "...", 0.40),
    ("IMG_3807.MOV", 0.96, 4.49,  "cta",      "...", 0.00),   # no gap before end card
]
```

`vo_dur(i)` now returns `(s_out - s_in) + gap_after`, so the cumulative VO timeline naturally lengthens by 1.6s (4 × 0.4s) to give 22.73s of audio.

In the render, each VO segment is extracted with a trailing silence padding:

```bash
ffmpeg -ss SIN -to SOUT -i SRC -vn \
  -af "apad=pad_dur=0.40" \
  -ac 2 -ar 48000 -c:a pcm_s16le vo_NN.wav
```

`apad` adds silent samples at the end so the file's duration equals `(audio + gap)`. Concatenating them gives a VO track with natural pauses between sentences.

### Visuals must hold through the breath

If the visual cuts on the exact instant the audio ends, the rhythm still feels rushed even with a silent gap. So the **last** cut of each VO segment is extended by `gap_after`:

```python
last_cut_for_vo = {}
for idx, cut in enumerate(CUTS):
    if cut[0] is not None:
        last_cut_for_vo[cut[0]] = idx

for idx, cut in enumerate(CUTS):
    vo_i, sub_o, sub_d, role, ff, src_in, label = cut
    if vo_i is not None and last_cut_for_vo[vo_i] == idx:
        sub_d += VO[vo_i][5]   # hold visual through the breath
```

### v7: reveal needs a longer source

The sanity check fired immediately:

> AssertionError: slot reveal: needs 2.83s from IMG_3820.MOV at src_in=0.00, only 2.50s available

`IMG_3820` is exactly 2.50s. Once we add the 0.40s breath, the slot needs 2.83s of footage. Swapped reveal to `IMG_3824.MOV` (7.17s — the same blue pagoda mat at an angled view). The CTA opener already uses IMG_3824 too, so to avoid showing identical frames the CTA opener was bumped to `src_in=4.0` while reveal stays at `src_in=0.0`. Different windows of the same clip.

### v7 → v8: hook lip-sync

User: "use IMG_3794 as the starting shot." I swapped the visual but kept the audio on IMG_3795 — and the lips no longer matched the words. Re-ran `silencedetect` on IMG_3794:

```
0.00 → 1.37   speech  "Rolling and action."
1.37 → 1.78   silence
1.78 → 5.05   speech  "The most beautiful mahjong set is finally here"
5.05 → 5.91   trailing silence
```

So 3794 has a clean read of the line at `1.78 → 5.05` (3.27s, basically identical length to the 3795 take). Set both audio and visual to IMG_3794 at src_in 1.78s and the lip-sync was perfect.

---

## v9 — Music nudged up

User: "what's the music? Can we bump it up 5%?"

Music identity: **Neiked – "Following the Sun"**. Volume `0.05 → 0.07` (about 40% relative bump, still well below VO). Everything else from v8 carries over. Locked.

---

## Appendix: the data model

```python
VO = [(clip, src_in, src_out, label, text, gap_after), ...]

CUTS = [(vo_index, sub_offset, sub_dur, role, force_file, force_src_in, label), ...]

CAPTIONS = {role: text_or_None}
```

- **VO** owns audio timing. Each entry produces one chunk of the audio bed (sentence + trailing silence). The last entry has `gap_after=0.0` so the audio ends cleanly before the logo card.
- **CUTS** owns visual timing. Cuts are anchored to a VO segment via `vo_index`; `sub_offset` and `sub_dur` are relative to that segment. Multiple cuts can sit inside one VO segment (e.g. four product visuals during the product-list line).
- **CAPTIONS** is keyed by role string. Currently all `None`; flip any value to a string and the render adds a centered caption band over that slot.
- **Sentinels**:
  - `force_file == "LOGO_END_CARD"` → emits a black slate with the brand logo and a fade-out (used as the post-VO closer).
  - `force_file == "WEBSITE_SCROLL"` → emits an animated top-to-bottom scroll of `assets/site_*.png` over the slot duration.
- **End card** is the only cut with `vo_index = None`. It lives in `post_offset` time, after the VO track ends.

---

## Appendix: the audio pipeline (locked)

```
01-source/IMG_xxxx.MOV ─┐
                        ├── extract VO segment with apad gap ─► vo_NN.wav
                        │
                        ├── (visual half: rendered into slot_NNN.mp4)
                        │
03-music/bed.wav  ──────┘   (trimmed + faded music)

Pass 1:  render each slot (1080×1920, silent)
Pass 1b: concat all vo_NN.wav → vo_concat.wav
Pass 2:  concat slot_NNN.mp4   → final video stream
         filter_complex:
             [bed]  highpass=250, volume=0.07
             [vo]   volume=1.0, asplit → [vo_mix], [vo_sc]
             [bed][vo_sc]    sidechaincompress(0.02, 20, 2, 350)  → [ducked]
             [ducked][vo_mix] amix(weights "1 8", normalize=0)    → [mix1]
             [mix1]           loudnorm(I=-16, LRA=11, TP=-1.5)    → [mix]
         → mux video + [mix], AAC 192k, +faststart
```

Target mean volume ≈ -19 dB, max ≈ -1.5 dB. Plays cleanly inside Instagram's auto-leveling.

---

## Appendix: gotchas

| Gotcha | Symptom | Mitigation |
|---|---|---|
| `silencedetect noise=-30dB` | Trims quiet word releases; whole phrases vanish | Use `-45dB / 0.25s`, then manually pick longest continuous burst |
| `-frames:v N` exceeds source | Slot silently truncates | Inventory-based sanity assertion in `build_reel.py` |
| `sidechaincompress` consumes its 2nd input | VO disappears from final mix | `asplit` the VO before feeding to compressor, then `amix` the survivor back in |
| Mac ffmpeg without `libfreetype` | `drawtext` filter not found | Render captions to PNG via ImageMagick, use `overlay` |
| `yt-dlp` over IPv6 | `No route to host` from YouTube search API | Force `-4` (IPv4) |
| Source clip ≤ slot duration + breath gap | Sanity check fires | Pick a longer source clip, or share one across slots with different `src_in` |
| Visual cuts on the exact instant audio ends | Reel feels rushed | Extend last cut of each VO by `gap_after` |
| Lip-sync mismatch when swapping a host shot | Lips move at wrong words | Match `src_in` between VO range and CUT |
