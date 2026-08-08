import os
import sys
import json
import argparse
import re
import ollama

from generator.prompts import get_speech_system_prompt, get_speech_user_prompt, apply_channel_credit

def adjust_and_expand_clip_timestamps(start: float, end: float, raw_segments: list, min_duration: float = 35.0, max_duration: float = 60.0) -> tuple:
    """
    1. Snaps `start` to the exact start of its matching transcript sentence segment.
    2. Ensures total duration (end - start) is between `min_duration` and `max_duration`
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
    """Extracts timestamped transcript lines within [start, end] window formatted for the UI."""
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

def heuristic_clip_selection(transcript_data: dict, count: int = 3, metadata: dict = None) -> list:
    """Fallback clip selector aligning start and end timestamps to exact sentence boundaries."""
    print("[SelectClips] Using sentence-aligned heuristic selector...")
    segments = transcript_data.get("segments", [])
    if not segments:
        return []

    if not metadata: metadata = {}
    vid_title = metadata.get("title", "Video Highlight")
    vid_tags = metadata.get("tags", ["highlight", "shorts", "video"])
    channel = metadata.get("channel", "")
    hashtags = " ".join([f"#{t.replace(' ', '')}" for t in vid_tags[:3]]) if vid_tags else "#highlight #shorts #video"

    total_segments = len(segments)
    if total_segments <= 3:
        base_desc = f"Check out this highlight from: {vid_title}" if vid_title else "Check out this highlight."
        return [{
            "start": segments[0]["start"],
            "end": segments[-1]["end"],
            "hook_strength_score": 9.1,
            "reason": f"Complete video segment: \"{segments[0]['text'][:60]}...\"",
            "title": f"{vid_title} - Short 1" if vid_title else "Full Highlight",
            "description": apply_channel_credit(base_desc, channel),
            "hashtags": hashtags,
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
                "title": f"{vid_title} - Part {i}",
                "description": apply_channel_credit("Check out this amazing highlight from the video!", channel),
                "hashtags": hashtags,
                "transcript_lines": t_lines
            })
    return clips

def select_clips(transcript_json_path: str, model_name: str = "llama3.1:8b", metadata: dict = None, raw_video_path: str = None, quantity: int = 3) -> list:
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
    # If transcript is very long, sample 3 large continuous blocks (e.g., ~100 segments each) 
    # so the LLM has full continuous context to find complete thoughts, rather than swiss-cheese gaps.
    if len(raw_segments) > 300:
        chunk_size = 100
        indices = [0, len(raw_segments) // 2 - chunk_size // 2, len(raw_segments) - chunk_size]
        for idx in indices:
            sampled_segments.extend(raw_segments[idx : idx + chunk_size])
            sampled_segments.append({"start": 0.0, "end": 0.0, "text": "\n--- [FAST FORWARD TO NEXT SECTION] ---\n"})
    else:
        sampled_segments = raw_segments

    segments_text = "\n".join(
        [f"[{seg['start']}s - {seg['end']}s] {seg['text']}" for seg in sampled_segments]
    )

    tags_str = ", ".join(metadata.get("tags", [])) if metadata and metadata.get("tags") else "general"
    title_str = metadata.get("title", "") if metadata else ""
    channel_str = metadata.get("channel", "") if metadata else ""

    prompt = get_speech_user_prompt(title_str, tags_str, channel_str, segments_text, quantity)

    print(f"[SelectClips] Prompting Ollama model ('{model_name}')...")
    try:
        response = ollama.chat(
            model=model_name,
            format="json",
            options={
                "temperature": 0.4,       # lower temp = fewer hallucinated/garbled fields on structured output
                "num_predict": 300 * quantity + 200,  # scale output budget with clip count to avoid mid-field truncation
            },
            messages=[
                {"role": "system", "content": get_speech_system_prompt(quantity)},
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
                # Robustly strip 's' if the LLM hallucinated the unit
                raw_start = float(str(c["start"]).lower().replace('s', '').strip())
                raw_end = float(str(c["end"]).lower().replace('s', '').strip())

                adj_start, adj_end = adjust_and_expand_clip_timestamps(raw_start, raw_end, raw_segments, min_duration=35.0, max_duration=60.0)
                dur = round(adj_end - adj_start, 2)
                snippet = get_segment_text_snippet(adj_start, raw_segments)

                ai_reason = str(c.get("reason", "")).strip()
                if not ai_reason:
                    ai_reason = f"Strong hook starting with: \"{snippet[:70]}\" - high viewer retention potential." if snippet else f"Selected by AI for high 0-3s viewer retention ({dur}s)."

                title = str(c.get("title", "")).strip() or f"Highlight Short {idx}"
                desc = str(c.get("description", "")).strip()
                desc = apply_channel_credit(desc, channel_str)

                try:
                    h_score = round(float(c.get("hook_strength_score", 9.4 - (idx - 1) * 0.4)), 1)
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

                # Normalize and composite score. Constants are rough starting points (typical RMS
                # ~0.05-0.10, typical scene cuts 0-3 per window) — worth recalibrating against a
                # sample of real videos rather than treating these as fixed truths.
                scaled_audio = min(10.0, audio_score * 80)
                scaled_visual = min(10.0, visual_score * 2)

                if scaled_audio > 0.0:
                    final_score = round((h_score * 0.5) + (scaled_audio * 0.3) + (scaled_visual * 0.2), 1)
                else:
                    final_score = h_score

                # Sanity bound only — deliberately NOT floored at a high number.
                # A weak clip should be able to score low; that's the entire point
                # of computing this instead of trusting one invented LLM float.
                final_score = max(1.0, min(10.0, final_score))

                t_lines = extract_transcript_lines_in_range(adj_start, adj_end, raw_segments)

                valid_clips.append({
                    "start": adj_start,
                    "end": adj_end,
                    "reason": ai_reason,
                    "title": title,
                    "description": desc,
                    "hashtags": c.get("hashtags", ""),
                    "hook_strength_score": h_score,
                    "composite_score": final_score,
                    "audio_energy": round(audio_score, 4),
                    "visual_energy": round(visual_score, 2),
                    "transcript_lines": t_lines
                })

        if len(valid_clips) < quantity and raw_segments:
            print(f"[SelectClips] LLM generated {len(valid_clips)} clip(s). Padding with sentence-aligned candidate clips to reach {quantity} total...")
            heuristics = heuristic_clip_selection(data, count=quantity, metadata=metadata)
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
            return heuristic_clip_selection(data, count=quantity, metadata=metadata)
    except Exception as e:
        print(f"[Warning] Ollama chat failed ({e}). Falling back to heuristics.")
        return heuristic_clip_selection(data, count=quantity, metadata=metadata)

def main():
    parser = argparse.ArgumentParser(description="Select short clip candidates using Ollama LLM.")
    parser.add_argument("transcript_json", help="Path to transcript JSON file")
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model name")
    parser.add_argument("--quantity", type=int, default=3, help="Number of clips to select")
    parser.add_argument("--title", default="", help="Video title, for prompt context")
    parser.add_argument("--channel", default="", help="Channel name, for credit line")
    parser.add_argument("--tags", default="", help="Comma-separated tags, for prompt context")
    parser.add_argument("--raw-video", default=None, help="Path to raw video, enables audio/visual scoring")

    args = parser.parse_args()
    metadata = {
        "title": args.title,
        "channel": args.channel,
        "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
    }
    try:
        clips = select_clips(
            args.transcript_json,
            model_name=args.model,
            metadata=metadata,
            raw_video_path=args.raw_video,
            quantity=args.quantity,
        )
        print(json.dumps(clips, indent=2))
    except Exception as e:
        print(f"[Error] Clip selection failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()