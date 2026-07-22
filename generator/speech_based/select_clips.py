import os
import sys
import json
import argparse
import re
import ollama

SYSTEM_PROMPT = """You are an expert short-form video editor selecting engaging clips for YouTube Shorts and Instagram Reels.
You will be provided with a timestamped transcript of a video.

Your task is to identify 2 to 4 high-value candidate clip segments.
Each clip MUST be between 15 seconds and 60 seconds long.
Look for:
- Strong opening hooks or compelling questions
- Self-contained points, tutorials, or stories
- Key takeaways or punchlines

Return ONLY a valid JSON array of objects with the exact keys: "start", "end", "reason", "title".
Example response format:
[
  {
    "start": 12.5,
    "end": 45.0,
    "reason": "Clear explanation of core concept with a strong opening hook.",
    "title": "Mastering the Core Concept in 30 Seconds"
  }
]
Do not include any conversational intro or markdown explanations outside the raw JSON array.
"""

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
            "reason": "Complete video transcript segment.",
            "title": "Full Highlight"
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
        
        if end_time - start_time >= 12.0:
            clips.append({
                "start": round(start_time, 2),
                "end": round(end_time, 2),
                "reason": f"Sentence-aligned segment starting at {int(start_time)}s.",
                "title": f"Highlight Clip {i}"
            })
    return clips

def select_clips(transcript_json_path: str, model_name: str = "llama3.1:8b") -> list:
    """
    Reads transcript JSON, prompts Ollama for candidate clip timestamps, and returns candidate clips.
    """
    if not os.path.exists(transcript_json_path):
        raise FileNotFoundError(f"Transcript JSON not found: {transcript_json_path}")
        
    with open(transcript_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    segments_text = "\n".join(
        [f"[{seg['start']}s - {seg['end']}s] {seg['text']}" for seg in data.get("segments", [])]
    )

    prompt = f"Video Title/Path: {data.get('video_path')}\nTotal Duration: {data.get('duration')}s\n\nTranscript Segments:\n{segments_text}"

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
        
        # Try direct JSON parse
        parsed_data = None
        try:
            parsed_data = json.loads(content)
        except Exception:
            # Extract JSON array or object using regex if wrapped in markdown
            json_match = re.search(r"(\[.*\]|\{.*\})", content, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group(0))

        clips = []
        if isinstance(parsed_data, list):
            clips = parsed_data
        elif isinstance(parsed_data, dict):
            # Find list value if wrapped in an object like {"clips": [...]}
            for key in ["clips", "candidates", "segments", "data"]:
                if key in parsed_data and isinstance(parsed_data[key], list):
                    clips = parsed_data[key]
                    break
            if not clips:
                # Take first list found in dict values
                for val in parsed_data.values():
                    if isinstance(val, list):
                        clips = val
                        break

        if clips:
            print(f"[SelectClips] LLM successfully selected {len(clips)} candidate clips.")
            return clips
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
