import os
import sys
from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector

def detect_visual_motion_scenes(video_path: str, threshold: float = 27.0) -> list:
    """
    Detects scene changes and visual motion moments in a video using PySceneDetect.
    Returns list of detected scenes [{start, end, duration}].
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    print(f"[MotionDetect] Running PySceneDetect on: {video_path}...")
    try:
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))

        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()

        results = []
        for scene in scene_list:
            start_sec = scene[0].get_seconds()
            end_sec = scene[1].get_seconds()
            duration = end_sec - start_sec
            results.append({
                "start": round(start_sec, 2),
                "end": round(end_sec, 2),
                "duration": round(duration, 2)
            })

        print(f"[MotionDetect] Detected {len(results)} visual scenes.")
        return results
    except Exception as e:
        print(f"[Warning] PySceneDetect failed ({e}). Returning empty motion list.")
        return []

def compute_visual_energy(video_path: str, start: float, end: float) -> float:
    """
    Computes visual energy (scene cuts per second) for a specific clip window.
    Extracts the window using ffmpeg and runs PySceneDetect.
    """
    import subprocess
    import tempfile
    import uuid
    import os

    try:
        tmp_mp4 = os.path.join(tempfile.gettempdir(), f"temp_{uuid.uuid4().hex}.mp4")
        # Extract low-res video chunk quickly using ffmpeg (no audio)
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(start), "-i", video_path, 
            "-t", str(end-start), "-an", "-s", "426x240", tmp_mp4
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        scenes = detect_visual_motion_scenes(tmp_mp4)
        if os.path.exists(tmp_mp4):
            os.remove(tmp_mp4)
            
        dur = end - start
        if dur <= 0: return 0.0
        
        # visual energy is (number of scenes) / (duration in seconds)
        # 1 cut per 5 seconds = 0.2 score. Let's scale it so it's a useful signal (0.0 to 1.0+)
        cut_frequency = len(scenes) / dur
        return float(cut_frequency * 10.0) # e.g. 0.2 cuts/sec -> 2.0 visual energy
    except Exception as e:
        print(f"[MotionDetect Error] Failed to compute visual energy for {start}-{end}: {e}")
        return 0.0
