import os
import sys
import numpy as np
import librosa

def detect_audio_energy_spikes(video_path: str, top_n: int = 5, min_clip_duration: float = 15.0) -> list:
    """
    Analyzes audio energy spikes (volume peaks) in a video using librosa.
    Returns list of candidate timestamp windows [{start, end, peak_time, energy_score}].
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    print(f"[AudioEnergy] Loading audio signal from: {video_path}...")
    try:
        y, sr = librosa.load(video_path, sr=22050, mono=True)
    except Exception as e:
        print(f"[Warning] Could not extract audio stream via librosa ({e}).")
        return []

    hop_length = 512
    frame_length = 2048
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

    # Convert frames to time seconds
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)

    # Threshold for energy peaks (e.g. > 1.5x mean energy)
    threshold = np.mean(rms) + (1.2 * np.std(rms))
    peak_indices = np.where(rms > threshold)[0]

    peaks = []
    for idx in peak_indices:
        t = times[idx]
        peaks.append((t, rms[idx]))

    # Sort peaks by energy score
    peaks.sort(key=lambda x: x[1], reverse=True)

    # Group close peaks to avoid duplicate ranges
    selected_ranges = []
    total_duration = librosa.get_duration(y=y, sr=sr)

    for peak_time, score in peaks:
        if len(selected_ranges) >= top_n:
            break

        start = max(0.0, peak_time - 15.0)
        end = min(total_duration, peak_time + 25.0)

        # Check overlap
        overlap = False
        for r in selected_ranges:
            if not (end < r["start"] or start > r["end"]):
                overlap = True
                break

        if not overlap and (end - start) >= min_clip_duration:
            selected_ranges.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "peak_time": round(peak_time, 2),
                "energy_score": round(float(score), 4)
            })

    print(f"[AudioEnergy] Identified {len(selected_ranges)} audio energy spike windows.")
    return selected_ranges

def compute_audio_energy(video_path: str, start: float, end: float) -> float:
    """
    Computes the average RMS audio energy of a specific video clip window.
    Uses ffmpeg to rapidly extract the specific window to a temporary wav file.
    """
    import subprocess
    import tempfile
    import uuid
    import os

    try:
        tmp_wav = os.path.join(tempfile.gettempdir(), f"temp_{uuid.uuid4().hex}.wav")
        # Extract audio chunk quickly using ffmpeg
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(start), "-i", video_path, 
            "-t", str(end-start), "-vn", "-ac", "1", "-ar", "22050", tmp_wav
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        y, sr = librosa.load(tmp_wav, sr=22050, mono=True)
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)
            
        if len(y) == 0:
            return 0.0
            
        rms = librosa.feature.rms(y=y)[0]
        return float(np.mean(rms))
    except Exception as e:
        print(f"[AudioEnergy Error] Failed to compute energy for {start}-{end}: {e}")
        return 0.0
