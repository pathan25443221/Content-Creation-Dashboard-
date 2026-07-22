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
