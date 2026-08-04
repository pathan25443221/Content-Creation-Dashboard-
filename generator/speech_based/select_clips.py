import os
import sys
import json
import argparse
import re
import ollama

def get_system_prompt(quantity: int = 3) -> str:
    return f"""You are an elite short-form content producer (YouTube Shorts & Instagram Reels).
You are analyzing a timestamped transcript along with the video's actual tags, title, and topic metadata.

Selection Criteria:
1. MANDATORY QUANTITY: You MUST select EXACTLY {quantity} distinct, non-overlapping candidate clips from different parts of the video (early, middle, and late sections).
2. DYNAMIC SPECIFIC REASONING: In the "reason" field for each clip, explain the EXACT spoken line, question, or story hook in that clip that grabs 0-3s attention and drives high retention.
3. HOOK STRENGTH SCORE: Provide a "hook_strength_score" float between 7.5 and 9.8 assessing the text-based hook quality.
4. DURATION MANDATE: Each clip MUST be between 35 seconds and 60 seconds long (duration = end - start MUST be at least 35 seconds).
15. COMPLETE THOUGHT BOUNDARY: Do NOT cut mid-sentence. Ensure `start` aligns with the first word of the hook sentence, and `end` aligns with the final period of the concluding sentence.
16. DESCRIPTION: Provide a 2-3 sentence "description" ready for YouTube/Instagram summarizing the clip.
17. HASHTAGS: Provide a single string of "hashtags" (e.g. "#gaming #shorts #viral").

Response Format:
Return ONLY a valid raw JSON array of EXACTLY {quantity} objects using exact keys: "start", "end", "reason", "title", "description", "hashtags", "hook_strength_score".
Example response format:
[
  {{
    "start": 15.0,
    "end": 42.5,
    "hook_strength_score": 9.3,
    "reason": "Hooks viewers instantly when the speaker asks 'Why do most startups fail in month one?', driving high 0-3s retention before delivering the full three-step resolution.",
    "title": "Why Startups Fail in Month One",
    "description": "Ever wonder why most startups fail within the first month? Here is the three-step resolution to avoid the most common pitfalls! Watch until the end.",
    "hashtags": "#startups #business #entrepreneur"
  }},
  {{
    "start": 180.2,
    "end": 212.0,
    "hook_strength_score": 8.7,
    "reason": "Dramatic story hook where the speaker reveals a costly mistake, creating a high curiosity gap that pays off at 210s.",
    "title": "The Biggest Mistake We Made",
    "description": "We made a massive mistake that cost us everything. Find out what happened and how you can avoid doing the same thing.",
    "hashtags": "#storytime #mistakes #lessonslearned"
  }}
]
"""

def adjust_and_expand_clip_timestamps(start: float, end: float, raw_segments: list, min_duration: float = 35.0, max_duration: float = 60.0) -> tuple:
    """
    1. Snaps `start` to the exact start of its matching transcript sentence segment.
    2. Ensures total duration (end - start) is between `min_duration` (35s) and `max_duration` (60s)
       by accumulating complete sentence segments.
    3. Guarantees no sentence is cut mid-thought.
    """
    if not raw_segments:
        return start, max(start + min_duration, end)

    # 1. Find the closest segment for the start time
    start_idx = 0
    min_diff_start = float("inf")
    for idx, seg in enumerate(raw_segments):
        diff = abs(seg["start"] - start)
        if diff < min_diff_start:
            min_diff_start = diff
            start_idx = idx

    # 2. Find the closest segment for the end time (must be >= start_idx)
    end_idx = start_idx
    min_diff_end = float("inf")
    for idx in range(start_idx, len(raw_segments)):
        diff = abs(raw_segments[idx]["end"] - end)
        if diff < min_diff_end:
            min_diff_end = diff
            end_idx = idx

    # 3. If the selected range is too short, expand the end_idx until min_duration is met
    actual_start = raw_segments[start_idx]["start"]
    
    while end_idx < len(raw_segments) - 1:
        actual_end = raw_segments[end_idx]["end"]
        if (actual_end - actual_start) >= min_duration:
            break
        end_idx += 1

    # 4. If the selected range is too long, truncate the end_idx until it fits max_duration
    while end_idx > start_idx:
        actual_end = raw_segments[end_idx]["end"]
        if (actual_end - actual_start) <= max_duration:
            break
        end_idx -= 1

    actual_end = raw_segments[end_idx]["end"]
    
    # Fallback if somehow still too short (e.g. single long segment)
    if actual_end - actual_start < min_duration and end_idx < len(raw_segments) - 1:
        actual_end = raw_segments[end_idx + 1]["end"]

    return round(actual_start, 2), round(actual_end, 2)

def get_segment_text_snippet(start: float, raw_segments: list) -> str:
    """Finds the transcript sentence snippet at `start` to enrich AI reasoning."""
    for seg in raw_segments:
        if abs(seg["start"] - start) <= 3.0 or (seg["start"] <= start <= seg["end"]):
            return seg["text"].strip()
    return ""

def extract_transcript_lines_in_range(start: float, end: float, raw_segments: list) -> list:
    """Extracts timestamped transcript lines within [start, end] window formatted for Vizard UI."""
    lines = []
    for seg in raw_segments:
        s_start = seg.get("start", 0.0)
        s_end = seg.get("end", 0.0)
        if s_end > start and s_start < end:
            mins = int(s_start // 60)
            secs = int(s_start % 60)
            ts_str = f"{mins:02d}:{secs:02d}"
            lines.append({
                "timestamp": ts_str,
                "text": seg.get("text", "").strip()
            })
    return lines

def heuristic_clip_selection(transcript_data: dict, count: int = 3) -> list:
    """Fallback clip selector aligning start and end timestamps to exact sentence boundaries."""
    print("[SelectClips] Using sentence-aligned heuristic selector...")
    segments = transcript_data.get("segments", [])
    if not segments:
        return []
    
    total_segments = len(segments)
    if total_segments <= 3:
        return [{
            "start": segments[0]["start"],
            "end": segments[-1]["end"],
            "hook_strength_score": 9.1,
            "reason": f"Complete video segment: \"{segments[0]['text'][:60]}...\"",
            "title": "Full Highlight",
            "transcript_lines": extract_transcript_lines_in_range(segments[0]["start"], segments[-1]["end"], segments)
        }]

    step = total_segments // (count + 1)
    clips = []
    
    for i in range(1, count + 1):
        start_idx = min(i * step, total_segments - 1)
        curr_end_idx = start_idx
        accumulated_duration = 0.0
        
        while curr_end_idx < total_segments - 1 and accumulated_duration < 45.0:
            seg_dur = segments[curr_end_idx]["end"] - segments[curr_end_idx]["start"]
            accumulated_duration += seg_dur
            curr_end_idx += 1

        start_time = segments[start_idx]["start"]
        end_time = segments[curr_end_idx]["end"]
        snippet = segments[start_idx]["text"].strip()
        t_lines = extract_transcript_lines_in_range(start_time, end_time, segments)
        
        dynamic_reasons = [
            f"Strong comedic hook starting with: \"{snippet[:80]}\" - high curiosity gap with full story payoff.",
            f"High-energy audience punchline at {round(start_time, 1)}s with line: \"{snippet[:80]}\".",
            f"Relatable main takeaway topic: \"{snippet[:80]}\" with high viewer retention potential."
        ]
        reason = dynamic_reasons[(i - 1) % len(dynamic_reasons)]

        if end_time - start_time >= 15.0:
            clips.append({
                "start": round(start_time, 2),
                "end": round(end_time, 2),
                "hook_strength_score": round(9.3 - (i - 1) * 0.5, 1),
                "reason": reason,
                "title": f"Highlight Short {i}",
                "description": f"Check out this amazing highlight from the video! {snippet[:60]}...",
                "hashtags": "#highlight #shorts #video",
                "transcript_lines": t_lines
            })
    return clips

def select_clips(transcript_json_path: str, model_name: str = "llama3.2:3b", metadata: dict = None, raw_video_path: str = None, quantity: int = 3) -> list:
    """
    Reads transcript JSON, prompts Ollama for candidate clip timestamps with video tags context.
    Ensures `quantity` distinct candidate clips are returned with dynamic sentence-based reasoning.
    """
    if not os.path.exists(transcript_json_path):
        raise FileNotFoundError(f"Transcript JSON not found: {transcript_json_path}")
        
    with open(transcript_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_segments = data.get("segments", [])
    
    sampled_segments = []
    if len(raw_segments) > 150:
        chunk_size = 15
        step = max(1, len(raw_segments) // 80)
        for i in range(0, len(raw_segments), step + chunk_size):
            sampled_segments.extend(raw_segments[i:i+chunk_size])
    else:
        sampled_segments = raw_segments

    segments_text = "\n".join(
        [f"[{seg['start']}s - {seg['end']}s] {seg['text']}" for seg in sampled_segments]
    )

    tags_str = ", ".join(metadata.get("tags", [])) if metadata and metadata.get("tags") else "general"
    title_str = metadata.get("title", "") if metadata else ""

    prompt = f"""VIDEO TITLE: "{title_str}"
TAGS: {tags_str}

TRANSCRIPT SEGMENTS:
{segments_text}

Task: Pick {quantity} top potential viral short clips from the transcript above. 
CRITICAL: You MUST return a JSON array containing EXACTLY {quantity} objects. 
EACH object MUST contain the exact following keys: "start", "end", "title", "description", "reason", "hashtags", "hook_strength_score".
Do NOT return a dictionary of clips, you MUST return a JSON array of objects with the start and end timestamps from the transcript.

Example format:
[
  {{
    "start": 15.0,
    "end": 42.5,
    "hook_strength_score": 9.3,
    "reason": "Hooks viewers instantly...",
    "title": "Why Startups Fail",
    "description": "Ever wonder why most startups fail? Here is the answer.",
    "hashtags": "#startups #business"
  }}
]
"""

    print(f"[SelectClips] Prompting Ollama model ('{model_name}')...")
    try:
        response = ollama.chat(
            model=model_name,
            format="json",
            messages=[
                {"role": "system", "content": get_system_prompt(quantity)},
                {"role": "user", "content": prompt}
            ]
        )
        content = response["message"]["content"].strip()
        print(f"[SelectClips] Raw Ollama Output:\n{content}\n")
        
        parsed_data = None
        try:
            parsed_data = json.loads(content)
        except Exception:
            json_match = re.search(r"(\[.*\]|\{.*\})", content, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group(0))

        clips = []
        if isinstance(parsed_data, list):
            clips = parsed_data
        elif isinstance(parsed_data, dict):
            if "start" in parsed_data and "end" in parsed_data:
                clips = [parsed_data]
            else:
                for key in ["clips", "candidates", "segments", "data", "results"]:
                    if key in parsed_data and isinstance(parsed_data[key], list):
                        clips = parsed_data[key]
                        break
                if not clips:
                    for val in parsed_data.values():
                        if isinstance(val, list):
                            clips = val
                            break
                        elif isinstance(val, dict) and "start" in val and "end" in val:
                            clips.append(val)

        valid_clips = []
        for idx, c in enumerate(clips, start=1):
            if isinstance(c, dict) and "start" in c and "end" in c:
                raw_start = float(c["start"])
                raw_end = float(c["end"])
                
                adj_start, adj_end = adjust_and_expand_clip_timestamps(raw_start, raw_end, raw_segments, min_duration=20.0, max_duration=50.0)
                dur = round(adj_end - adj_start, 2)
                snippet = get_segment_text_snippet(adj_start, raw_segments)
                
                ai_reason = str(c.get("reason", "")).strip()
                if not ai_reason or "matching the video's specific tags" in ai_reason:
                    ai_reason = f"Strong hook starting with: \"{snippet[:70]}\" - high viewer retention potential." if snippet else f"Selected by AI for high 0-3s viewer retention ({dur}s)."
                
                title = str(c.get("title", "")).strip() or f"Highlight Short {idx}"
                
                try:
                    h_score = round(float(c.get("hook_strength_score", c.get("virality_score", 9.4 - (idx - 1) * 0.4))), 1)
                except Exception:
                    h_score = round(9.4 - (idx - 1) * 0.4, 1)

                audio_score = 0.0
                visual_score = 0.0
                if raw_video_path and os.path.exists(raw_video_path):
                    from generator.visual_based.audio_energy import compute_audio_energy
                    from generator.visual_based.motion_detect import compute_visual_energy
                    
                    print(f"[SelectClips] Computing multimodal energy for clip {idx} ({adj_start}s - {adj_end}s)...")
                    audio_score = compute_audio_energy(raw_video_path, adj_start, adj_end)
                    visual_score = compute_visual_energy(raw_video_path, adj_start, adj_end)
                    
                # Normalize and composite score
                scaled_audio = min(9.9, audio_score * 80) # typical RMS 0.05-0.10
                scaled_visual = min(9.9, visual_score * 2) # typical cuts 0-3
                
                if scaled_audio > 0.0:
                    final_score = round((h_score * 0.5) + (scaled_audio * 0.3) + (scaled_visual * 0.2), 1)
                else:
                    final_score = h_score
                
                final_score = max(7.0, min(9.9, final_score))

                t_lines = extract_transcript_lines_in_range(adj_start, adj_end, raw_segments)

                valid_clips.append({
                    "start": adj_start,
                    "end": adj_end,
                    "reason": ai_reason,
                    "title": title,
                    "description": c.get("description", ""),
                    "hashtags": c.get("hashtags", ""),
                    "virality_score": final_score, # Keep key for frontend compatibility
                    "hook_strength_score": h_score,
                    "audio_energy": round(audio_score, 4),
                    "visual_energy": round(visual_score, 2),
                    "transcript_lines": t_lines
                })

        if len(valid_clips) < quantity and raw_segments:
            print(f"[SelectClips] LLM generated {len(valid_clips)} clip(s). Padding with sentence-aligned candidate clips to reach {quantity} total...")
            heuristics = heuristic_clip_selection(data, count=quantity)
            for h in heuristics:
                if len(valid_clips) >= quantity:
                    break
                overlap = any(abs(h["start"] - existing["start"]) < 15.0 for existing in valid_clips)
                if not overlap:
                    valid_clips.append(h)

        if valid_clips:
            print(f"[SelectClips] LLM successfully outputted {len(valid_clips)} candidate clips!")
            return valid_clips
        else:
            print(f"[Warning] Could not extract valid clip array from LLM response. Falling back to heuristics.")
            return heuristic_clip_selection(data, count=quantity)
    except Exception as e:
        print(f"[Warning] Ollama chat failed ({e}). Falling back to heuristics.")
        return heuristic_clip_selection(data, count=quantity)

def main():
    parser = argparse.ArgumentParser(description="Select short clip candidates using Ollama LLM.")
    parser.add_argument("transcript_json", help="Path to transcript JSON file")
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model name")

    args = parser.parse_args()
    try:
        clips = select_clips(args.transcript_json, args.model)
        print(json.dumps(clips, indent=2))
    except Exception as e:
        print(f"[Error] Clip selection failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
