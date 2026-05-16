"""
Beat / structure analysis for cherry_lady_full.wav.

Outputs beat_grid.json with: bpm, total_duration, beat_times, chorus_start_sec,
chorus_end_sec, window_start_sec, window_end_sec, beats_in_window.
"""

from __future__ import annotations

import json
from pathlib import Path

import librosa
import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE / "cherry_lady_full.wav"
OUT = HERE / "beat_grid.json"

WINDOW_SEC = 30.0


def main() -> None:
    # Load mono at native sample rate (librosa resamples to 22050 by default;
    # that's fine for beat tracking and faster).
    y, sr = librosa.load(str(SRC), sr=22050, mono=True)
    total_duration = float(librosa.get_duration(y=y, sr=sr))

    # Global tempo + beat frames
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    bpm = float(np.atleast_1d(tempo)[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).astype(float)

    # Onset envelope (for peak hits info, also feeds tempo/beat tracking)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_peaks_frames = librosa.util.peak_pick(
        onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.5, wait=10
    )
    onset_peak_times = librosa.frames_to_time(onset_peaks_frames, sr=sr).astype(float)

    # RMS energy on short windows
    hop_length = 512
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)

    # Smooth RMS with ~2-second moving average to find sustained loud sections
    win_frames = max(1, int(round(2.0 * sr / hop_length)))
    kernel = np.ones(win_frames, dtype=np.float32) / win_frames
    rms_smooth = np.convolve(rms, kernel, mode="same")

    # Find the loudest sustained section -> proxy for chorus
    # Slide a WINDOW_SEC window across rms_smooth and find the start
    # that maximizes the mean smoothed RMS.
    win_rms_frames = max(1, int(round(WINDOW_SEC * sr / hop_length)))
    if win_rms_frames >= len(rms_smooth):
        best_start_frame = 0
    else:
        cumulative = np.concatenate([[0.0], np.cumsum(rms_smooth)])
        window_sums = cumulative[win_rms_frames:] - cumulative[:-win_rms_frames]
        best_start_frame = int(np.argmax(window_sums))
    window_start_raw = float(rms_times[best_start_frame])
    window_end_raw = window_start_raw + WINDOW_SEC

    # Identify the chorus region: contiguous span around peak RMS above a threshold
    peak_frame = int(np.argmax(rms_smooth))
    peak_val = float(rms_smooth[peak_frame])
    threshold = 0.85 * peak_val  # within 15% of peak counts as "chorus-loud"
    above = rms_smooth >= threshold

    # Walk left/right from peak while still above threshold (allow short dips of <1s)
    max_gap = max(1, int(round(1.0 * sr / hop_length)))

    def expand(start: int, direction: int) -> int:
        idx = start
        gap = 0
        while 0 <= idx + direction < len(above):
            idx += direction
            if above[idx]:
                gap = 0
            else:
                gap += 1
                if gap > max_gap:
                    idx -= direction * gap
                    break
        return idx

    chorus_start_frame = expand(peak_frame, -1)
    chorus_end_frame = expand(peak_frame, +1)
    chorus_start_sec = float(rms_times[max(0, chorus_start_frame)])
    chorus_end_sec = float(rms_times[min(len(rms_times) - 1, chorus_end_frame)])

    # Snap window to nearest beats so loops are clean.
    def snap_to_beat(t: float) -> float:
        if len(beat_times) == 0:
            return t
        i = int(np.argmin(np.abs(beat_times - t)))
        return float(beat_times[i])

    window_start_sec = snap_to_beat(window_start_raw)
    # Snap end to keep duration ~30s but on a beat too
    window_end_sec_target = window_start_sec + WINDOW_SEC
    window_end_sec = snap_to_beat(window_end_sec_target)
    # If snapping pulled end too far from 30s, just hard-cut to 30s
    if abs((window_end_sec - window_start_sec) - WINDOW_SEC) > 0.25:
        window_end_sec = window_start_sec + WINDOW_SEC

    beats_in_window = [
        float(t - window_start_sec)
        for t in beat_times
        if window_start_sec <= t <= window_end_sec
    ]

    payload = {
        "source_file": SRC.name,
        "sample_rate_analysis": sr,
        "bpm": round(bpm, 3),
        "total_duration": round(total_duration, 3),
        "beat_times": [round(t, 4) for t in beat_times.tolist()],
        "onset_peak_times": [round(t, 4) for t in onset_peak_times.tolist()],
        "chorus_start_sec": round(chorus_start_sec, 3),
        "chorus_end_sec": round(chorus_end_sec, 3),
        "rms_peak_sec": round(float(rms_times[peak_frame]), 3),
        "rms_peak_value": round(peak_val, 5),
        "window_start_sec": round(window_start_sec, 3),
        "window_end_sec": round(window_end_sec, 3),
        "window_duration_sec": round(window_end_sec - window_start_sec, 3),
        "beats_in_window": [round(t, 4) for t in beats_in_window],
        "beat_count_in_window": len(beats_in_window),
    }

    OUT.write_text(json.dumps(payload, indent=2))
    print(
        f"BPM={bpm:.2f}  duration={total_duration:.2f}s  "
        f"chorus={chorus_start_sec:.2f}-{chorus_end_sec:.2f}  "
        f"window={window_start_sec:.2f}-{window_end_sec:.2f}  "
        f"beats_in_window={len(beats_in_window)}"
    )


if __name__ == "__main__":
    main()
