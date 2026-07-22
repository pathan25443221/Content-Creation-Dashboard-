import os
import sys
import json
import argparse
from generator.visual_based.audio_energy import detect_audio_energy_spikes
from generator.visual_based.motion_detect import detect_visual_motion_scenes

def select_visual_clips(video_path: str, target_count: int = 3) -> list:
    """
    Combines audio energy spikes and visual scene motion into 2–4 candidate clip timestamps.
    Returns list of dicts: [{start, end, reason, title}].
    """
    audio_spikes = detect_audio_energy_spikes(video_path, top_n=target_count * 2)
    scenes = detect_visual_motion_scenes(video_path)

    candidates = []

    # Priority 1: High audio energy spike combined with visual motion scene
    if audio_spikes:
        for idx, spike in enumerate(audio_spikes[:target_count], start=1):
            candidates.append({
                "start": spike["start"],
                "end": spike["end"],
                "reason": f"Audio energy volume spike (crowd/impact) detected around {spike['peak_time']}s.",
                "title": f"Action Highlight {idx}"
            })
    
    # Priority 2: High motion scene if audio energy yielded fewer than target_count
    if len(candidates) < target_count and scenes:
        for idx, scene in enumerate(scenes, start=1):
            if len(candidates) >= target_count:
                break
            if scene["duration"] >= 15.0:
                # Check overlap with existing
                overlap = False
                for c in candidates:
                    if not (scene["end"] < c["start"] or scene["start"] > c["end"]):
                        overlap = True
                        break
                if not overlap:
                    candidates.append({
                        "start": scene["start"],
                        "end": min(scene["end"], scene["start"] + 45.0),
                        "reason": f"Visual motion & scene cut sequence ({scene['duration']}s duration).",
                        "title": f"Scene Highlight {len(candidates) + 1}"
                    })

    # Priority 3: Fallback uniform windowing if no spikes/scenes detected
    if not candidates:
        print("[VisualSelect] No distinct spikes detected. Using fallback windowing...")
        candidates = [
            {"start": 10.0, "end": 40.0, "reason": "Visual highlight segment 10s-40s.", "title": "Visual Highlight 1"},
            {"start": 45.0, "end": 75.0, "reason": "Visual highlight segment 45s-75s.", "title": "Visual Highlight 2"}
        ]

    print(f"[VisualSelect] Outputting {len(candidates)} visual path candidate clips.")
    return candidates

def main():
    parser = argparse.ArgumentParser(description="Select candidate clips from visual/non-speech content.")
    parser.add_argument("video_path", help="Path to raw mp4 file")
    parser.add_argument("--count", type=int, default=3, help="Number of clips to select")

    args = parser.parse_args()
    try:
        clips = select_visual_clips(args.video_path, args.count)
        print(json.dumps(clips, indent=2))
    except Exception as e:
        print(f"[Error] Visual clip selection failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
