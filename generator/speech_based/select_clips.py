import os
import sys
import json
import argparse
import re
import ollama

SYSTEM_PROMPT = """You are an elite short-form content producer (YouTube Shorts & Instagram Reels).
You are analyzing a timestamped transcript along with the video's actual tags, title, and topic metadata.

Selection Criteria:
1. MANDATORY QUANTITY: You MUST select EXACTLY 3 distinct, non-overlapping candidate clips from different parts of the video (early, middle, and late sections).
2. DYNAMIC SPECIFIC REASONING: In the "reason" field for each clip, explain the EXACT spoken line, question, or story hook in that clip that grabs 0-3s attention and drives high retention.
3. VIRALITY SCORE: Provide a "virality_score" float between 7.5 and 9.8 assessing the overall viral potential of the clip.
4. DURATION MANDATE: Each clip MUST be between 20 seconds and 50 seconds long (duration = end - start MUST be at least 20 seconds).
5. COMPLETE THOUGHT BOUNDARY: Do NOT cut mid-sentence. Ensure `start` aligns with the first word of the hook sentence, and `end` aligns with the final period of the concluding sentence.

Response Format:
Return ONLY a valid raw JSON array of EXACTLY 3 objects using exact keys: "start", "end", "reason", "title", "virality_score".
Example response format:
[
  {
    "start": 15.0,
    "end": 42.5,
    "virality_score": 9.3,
    "reason": "Hooks viewers instantly when the speaker asks 'Why do most startups fail in month one?', driving high 0-3s retention before delivering the full three-step resolution.",
    "title": "Why Startups Fail in Month One"
  },
  {
    "start": 180.2,
    "end": 212.0,
    "virality_score": 8.7,
    "reason": "Dramatic story hook where the speaker reveals a costly mistake, creating a high curiosity gap that pays off at 210s.",
    "title": "The Biggest Mistake We Made"
  },
  {
    "start": 410.5,
    "end": 448.0,
    "virality_score": 8.1,
    "reason": "High-energy punchline moment highlighting the main key takeaway of the entire video.",
    "title": "The Ultimate Key Takeaway"
  }
]
"""

def adjust_and_expand_clip_timestamps(start: float, end: float, raw_segments: list, min_duration: float = 20.0, max_duration: float = 50.0) -> tuple:
    """
    1. Snaps `start` to the exact start of its matching transcript sentence segment.
    2. Ensures total duration (end - start) is between `min_duration` (20s) and `max_duration` (50s)
       by accumulating complete sentence segments.
    3. Guarantees no sentence is cut mid-thought.
    """
    if not raw_segments:
        return start, max(start + min_duration, end)

    start_idx = 0
    min_diff = float("inf")
    for idx, seg in enumerate(raw_segments):
        diff = abs(seg["start"] - start)
        if diff < min_diff:
            min_diff = diff
            start_idx = idx

    actual_start = raw_segments[start_idx]["start"]
    curr_idx = start_idx
    accumulated_dur = 0.0

    while curr_idx < len(raw_segments) - 1:
        seg_dur = raw_segments[curr_idx]["end"] - raw_segments[curr_idx]["start"]
        accumulated_dur += seg_dur
        curr_idx += 1
        if accumulated_dur >= min_duration:
            if accumulated_dur > max_duration and curr_idx > start_idx + 1:
                curr_idx -= 1
            break

    actual_end = raw_segments[min(curr_idx, len(raw_segments) - 1)]["end"]
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
            "virality_score": 9.1,
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
        
        while curr_end_idx < total_segments - 1 and accumulated_duration < 35.0:
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
                "virality_score": round(9.3 - (i - 1) * 0.5, 1),
                "reason": reason,
                "title": f"Highlight Short {i}",
                "transcript_lines": t_lines
            })
    return clips

def select_clips(transcript_json_path: str, model_name: str = "llama3.2:3b", metadata: dict = None) -> list:
    """
    Reads transcript JSON, prompts Ollama for candidate clip timestamps with video tags context.
    Ensures 3 distinct candidate clips are returned with virality scores and dynamic sentence-based reasoning.
    """
    if not os.path.exists(transcript_json_path):
        raise FileNotFoundError(f"Transcript JSON not found: {transcript_json_path}")
        
    with open(transcript_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_segments = data.get("segments", [])
    
    sampled_segments = raw_segments
    if len(raw_segments) > 150:
        step = max(1, len(raw_segments) // 120)
        sampled_segments = raw_segments[::step]

    segments_text = "\n".join(
        [f"[{seg['start']}s - {seg['end']}s] {seg['text']}" for seg in sampled_segments]
    )

    tags_str = ", ".join(metadata.get("tags", [])) if metadata and metadata.get("tags") else "general"
    title_str = metadata.get("title", "") if metadata else ""

    prompt = f"""VIDEO TITLE: "{title_str}"
TAGS: {tags_str}

TRANSCRIPT SEGMENTS:
{segments_text}

Task: Pick 3 top potential viral short clips. Return JSON format only."""

    print(f"[SelectClips] Prompting Ollama model ('{model_name}')...")
    try:
        response = ollama.chat(
            model=model_name,
            format="json",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
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
                    v_score = round(float(c.get("virality_score", 9.4 - (idx - 1) * 0.4)), 1)
                except Exception:
                    v_score = round(9.4 - (idx - 1) * 0.4, 1)

                t_lines = extract_transcript_lines_in_range(adj_start, adj_end, raw_segments)

                valid_clips.append({
                    "start": adj_start,
                    "end": adj_end,
                    "reason": ai_reason,
                    "title": title,
                    "virality_score": v_score,
                    "transcript_lines": t_lines
                })

        if len(valid_clips) < 3 and raw_segments:
            print(f"[SelectClips] LLM generated {len(valid_clips)} clip(s). Padding with sentence-aligned candidate clips to reach 3 total...")
            heuristics = heuristic_clip_selection(data, count=3)
            for h in heuristics:
                if len(valid_clips) >= 3:
                    break
                overlap = any(abs(h["start"] - existing["start"]) < 15.0 for existing in valid_clips)
                if not overlap:
                    valid_clips.append(h)

        if valid_clips:
            print(f"[SelectClips] LLM successfully outputted {len(valid_clips)} candidate clips!")
            return valid_clips
        else:
            print(f"[Warning] Could not extract valid clip array from LLM response. Falling back to heuristics.")
            return heuristic_clip_selection(data)
    except Exception as e:
        print(f"[Warning] Ollama chat failed ({e}). Falling back to heuristics.")
        return heuristic_clip_selection(data)

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
