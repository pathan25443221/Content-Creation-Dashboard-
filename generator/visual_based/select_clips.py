import os
import sys
import json
import argparse
from generator.visual_based.audio_energy import detect_audio_energy_spikes
from generator.visual_based.motion_detect import detect_visual_motion_scenes
from generator.prompts import get_visual_metadata_prompt, get_visual_metadata_system_prompt

def select_visual_clips(video_path: str, target_count: int = 3, metadata: dict = None, transcript_json: dict = None) -> list:
    """
    Combines audio energy spikes and visual scene motion into candidate clip timestamps.
    If transcript_json is provided, snaps clips to sentence boundaries.
    Returns list of dicts: [{start, end, reason, title, description, hashtags}].
    """
    audio_spikes = detect_audio_energy_spikes(video_path, top_n=target_count * 2)
    scenes = detect_visual_motion_scenes(video_path)

    candidates = []

    channel_str = metadata.get("channel", "") if metadata else ""
    credit_suffix = f" Credit to {channel_str}." if channel_str else ""

    # Priority 1: High audio energy spike
    if audio_spikes:
        base_title = metadata.get("title", "Action Highlight").replace(".mp4", "") if metadata else "Action Highlight"
        for idx, spike in enumerate(audio_spikes[:target_count], start=1):
            candidates.append({
                "start": spike["start"],
                "end": spike["end"],
                "reason": f"Audio energy volume spike (crowd/impact) detected around {spike['peak_time']}s.",
                "title": f"{base_title} - Part {idx}",
                "description": f"Epic action and hype moment! You don't want to miss this.{credit_suffix}",
                "hashtags": "#action #hype #gaming #shorts"
            })
    
    # Priority 2: High motion scene if audio energy yielded fewer than target_count
    if len(candidates) < target_count and scenes:
        base_title = metadata.get("title", "Scene Highlight").replace(".mp4", "") if metadata else "Scene Highlight"
        for idx, scene in enumerate(scenes, start=1):
            if len(candidates) >= target_count:
                break
            if scene["duration"] >= 15.0:
                overlap = False
                for c in candidates:
                    if not (scene["end"] < c["start"] or scene["start"] > c["end"]):
                        overlap = True
                        break
                if not overlap:
                    candidates.append({
                        "start": scene["start"],
                        "end": max(scene["end"], scene["start"] + 40.0),
                        "reason": f"Visual motion & scene cut sequence ({scene['duration']}s duration).",
                        "title": f"{base_title} - Part {len(candidates) + 1}",
                        "description": f"Awesome visual sequence. Check out this highlight!{credit_suffix}",
                        "hashtags": "#highlight #visuals #gaming"
                    })

    # Priority 3: Fallback uniform windowing if no spikes/scenes detected
    if not candidates:
        print("[VisualSelect] No distinct spikes detected. Using fallback windowing...")
        base_title = metadata.get("title", "Visual Highlight").replace(".mp4", "") if metadata else "Visual Highlight"
        for i in range(target_count):
            start = 10.0 + (i * 35.0)
            candidates.append({
                "start": start,
                "end": start + 40.0,
                "reason": f"Visual highlight segment {start}s-{start+40.0}s.",
                "title": f"{base_title} - Part {i+1}",
                "description": f"Amazing visual highlight clip! Enjoy the action.{credit_suffix}",
                "hashtags": "#highlight #shorts #action"
            })

    # Hybrid Step: Snap timestamps to transcript boundaries
    if transcript_json and candidates:
        try:
            if isinstance(transcript_json, str):
                import json
                with open(transcript_json, "r", encoding="utf-8") as f:
                    transcript_json = json.load(f)
                    
            from generator.speech_based.select_clips import adjust_and_expand_clip_timestamps, get_segment_text_snippet
            raw_segments = transcript_json.get("segments", [])
            if raw_segments:
                print(f"[VisualSelect] Snapping {len(candidates)} visual clips to sentence boundaries...")
                for c in candidates:
                    adj_start, adj_end = adjust_and_expand_clip_timestamps(c["start"], max(c["end"], c["start"] + 35.0), raw_segments, min_duration=30.0, max_duration=60.0)
                    snippet = get_segment_text_snippet(adj_start, raw_segments)
                    c["start"] = adj_start
                    c["end"] = adj_end
                    c["transcript_snippet"] = snippet
                    if snippet:
                        c["reason"] += f" Transcript at spike: '{snippet[:60]}...'"
        except Exception as e:
            print(f"[Warning] Failed to snap visual clips to transcript: {e}")

    # AI Enhancement: Generate unique viral titles/descriptions if metadata is available
    if metadata and candidates:
        try:
            import ollama
            import re
            
            title_str = metadata.get("title", "Gaming Video")
            tags_str = ", ".join(metadata.get("tags", [])) if metadata.get("tags") else "gaming, action"
            channel_str = metadata.get("channel", "")
            
            prompt = get_visual_metadata_prompt(title_str, tags_str, channel_str, candidates, transcript_json)
            
            
            response = ollama.chat(
                model="llama3.1:8b", # match the speech pipeline's more capable model
                format="json",
                options={
                    "temperature": 0.4,
                    "num_predict": 300 * len(candidates) + 200,
                },
                messages=[
                    {"role": "system", "content": get_visual_metadata_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response["message"]["content"].strip()
            
            parsed_data = None
            try:
                parsed_data = json.loads(content)
            except Exception:
                json_match = re.search(r"(\[.*\]|\{.*\})", content, re.DOTALL)
                if json_match:
                    parsed_data = json.loads(json_match.group(1))
                    
            ai_clips = []
            if isinstance(parsed_data, list):
                ai_clips = [c for c in parsed_data if isinstance(c, dict)]
            elif isinstance(parsed_data, dict):
                # Check if it's a single clip object itself
                if "title" in parsed_data and "description" in parsed_data:
                    ai_clips = [parsed_data]
                else:
                    for key in ["clips", "candidates", "data", "results"]:
                        if key in parsed_data and isinstance(parsed_data[key], list):
                            ai_clips = [c for c in parsed_data[key] if isinstance(c, dict)]
                            break
                    if not ai_clips:
                        for val in parsed_data.values():
                            if isinstance(val, dict) and ("title" in val or "description" in val):
                                ai_clips.append(val)
                            elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                                ai_clips = val
                                break
                            
            if ai_clips:
                print(f"[VisualSelect] Successfully enhanced {min(len(candidates), len(ai_clips))} clips with LLM metadata.")
                for i in range(min(len(candidates), len(ai_clips))):
                    candidates[i]["title"] = ai_clips[i].get("title", candidates[i]["title"])
                    candidates[i]["description"] = ai_clips[i].get("description", candidates[i]["description"])
                    candidates[i]["hashtags"] = ai_clips[i].get("hashtags", candidates[i]["hashtags"])
            else:
                print(f"[Warning] AI metadata array was empty or failed to parse. Using fallback.")
        except Exception as e:
            print(f"[Warning] Failed to generate AI metadata for visual clips: {e}")

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
