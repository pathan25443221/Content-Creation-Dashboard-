import os
import sys
import json
import argparse
import subprocess

def generate_ass_subtitles(transcript_json_path: str, start: float, end: float, ass_out_path: str, animation: str = "none", color: str = "&H00FFFFFF") -> bool:
    """
    Generates an ASS file for the specific clip window to support advanced TikTok animations like pop and fade.
    """
    if not transcript_json_path or not os.path.exists(transcript_json_path):
        return False
        
    try:
        with open(transcript_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        segments = data.get("segments", [])
        clip_segments = []
        
        for seg in segments:
            s_start = seg["start"]
            s_end = seg["end"]
            if s_end > start and s_start < end:
                rel_start = max(0.0, s_start - start)
                rel_end = min(end - start, s_end - start)
                if rel_end > rel_start:
                    clip_segments.append({
                        "start": rel_start,
                        "end": rel_end,
                        "text": seg["text"].strip()
                    })

        if not clip_segments:
            return False

        def format_timestamp(seconds: float) -> str:
            # ASS format: H:MM:SS.cs (cs = centiseconds 0-99)
            cs = int((seconds % 1) * 100)
            secs = int(seconds)
            mins = secs // 60
            hours = mins // 60
            mins = mins % 60
            secs = secs % 60
            return f"{hours}:{mins:02d}:{secs:02d}.{cs:02d}"

        # ASS Header
        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,65,{color},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,0,2,10,10,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        with open(ass_out_path, "w", encoding="utf-8") as f:
            f.write(ass_header)
            for seg in clip_segments:
                start_ts = format_timestamp(seg['start'])
                end_ts = format_timestamp(seg['end'])
                text = seg['text'].replace('\n', '\\N')
                
                # Inject ASS tags if animation is requested
                if animation == "pop":
                    # TikTok pop: starts at 50% scale, quickly pops to 110%, then settles to 100%
                    # Actually, a simple 50% to 100% over 100ms works well
                    text = f"{{\\fscx50\\fscy50\\t(0,100,\\fscx100\\fscy100)}}{text}"
                elif animation == "fade":
                    text = f"{{\\fad(200,200)}}{text}"
                    
                f.write(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{text}\n")

        return True
    except Exception as e:
        print(f"[Warning] Failed to generate ASS subtitles: {e}", file=sys.stderr)
        return False

def render_clip(video_path: str, start: float, end: float, output_path: str, transcript_json_path: str = None, x_ratio: float = 0.5, y_ratio: float = 0.5, w_ratio: float = 0.0, h_ratio: float = 0.0, layout_mode: str = "visual_split", quality: str = "high", dynamic_ratios: list = None, caption_color: str = "white", caption_animation: str = "none") -> str:
    """
    Renders a vertical 9:16 clip from raw video between start and end timestamps using ffmpeg.
    If layout_mode is visual_split, uses a split-screen layout (gameplay top, face bottom).
    Otherwise, uses a standard 9:16 full-height crop tracking the face or centered.
    Burns subtitles if transcript JSON is provided.
    quality determines FFmpeg encoding parameters (high, medium, low).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    duration = end - start

    if layout_mode == "vlog" and dynamic_ratios:
        # Dynamic framing: Split the already-trimmed input video into 1s chunks and crop each dynamically
        filter_complex = ""
        for i, chunk in enumerate(dynamic_ratios):
            c_start = max(0, chunk["start"] - start)
            c_end = min(duration, chunk["end"] - start)
            # Full height crop, but dynamic X
            fx = f"max(0\\,min(iw-ih*(9/16)\\,iw*{chunk['x_ratio']}-ih*(9/16)/2))"
            filter_complex += f"[0:v]trim=start={c_start}:end={c_end},setpts=PTS-STARTPTS,crop=ih*(9/16):ih:{fx}:0[v{i}];"
        
        # Concat all the chunks
        concat_inputs = "".join([f"[v{i}]" for i in range(len(dynamic_ratios))])
        filter_complex += f"{concat_inputs}concat=n={len(dynamic_ratios)}:v=1:a=0[stacked]"

    elif layout_mode == "visual_split" and dynamic_ratios:
        # Split screen with dynamic tracking for the bottom screen
        filter_complex = ""
        for i, chunk in enumerate(dynamic_ratios):
            c_start = max(0, chunk["start"] - start)
            c_end = min(duration, chunk["end"] - start)
            
            # Top crop (static center for gameplay)
            top_crop = f"crop=ih*(9/16):ih/2:(iw-ih*(9/16))/2:(ih-ih/2)/2"
            
            # Bottom crop (dynamic Face Cam)
            fx = f"max(0\\,min(iw-ih*(9/16)\\,iw*{chunk['x_ratio']}-ih*(9/16)/2))"
            fy = f"max(0\\,min(ih-ih/2\\,ih*{chunk['y_ratio']}-ih/4))"
            bottom_crop = f"crop=ih*(9/16):ih/2:{fx}:{fy}"
            
            filter_complex += f"[0:v]trim=start={c_start}:end={c_end},setpts=PTS-STARTPTS,split=2[top_src{i}][bot_src{i}];"
            filter_complex += f"[top_src{i}]{top_crop}[top{i}];"
            filter_complex += f"[bot_src{i}]{bottom_crop}[bot{i}];"
            filter_complex += f"[top{i}][bot{i}]vstack=inputs=2[v{i}];"
            
        # Concat all the chunks
        concat_inputs = "".join([f"[v{i}]" for i in range(len(dynamic_ratios))])
        filter_complex += f"{concat_inputs}concat=n={len(dynamic_ratios)}:v=1:a=0[stacked]"

    elif layout_mode == "visual_split":
        # Static split screen fallback (Top is 65%, Bottom is 35%)
        top_crop = "crop=ih*(9/16):ih*0.65:(iw-ih*(9/16))/2:(ih-ih*0.65)/2"
        
        w_ratio = locals().get("w_ratio", 0)
        h_ratio = locals().get("h_ratio", 0)
        
        # Bottom aspect ratio = (9/16) / 0.35 = 1.60714
        bot_aspect = (9/16) / 0.35
        
        if w_ratio > 0 and h_ratio > 0:
            # To keep the person PERFECTLY centered, the crop must not hit the video edges.
            max_crop_w = f"(2*min({x_ratio}\\, 1.0-{x_ratio})*iw)"
            max_crop_h = f"(2*min({y_ratio}\\, 1.0-{y_ratio})*ih)"
            
            # Convert max_crop_w to an equivalent height limit based on the aspect ratio
            max_h_from_w = f"({max_crop_w}/{bot_aspect})"
            
            # The absolute maximum crop_h that won't hit any edges
            max_allowed_h = f"min({max_crop_h}\\, {max_h_from_w})"
            
            # The target crop height is 4x the face height for a comfortable safe distance
            target_crop_h = f"(ih*min(1.0\\, max(0.2\\, {h_ratio}*4.0)))"
            
            # The absolute minimum crop height so we don't cut off the face itself
            min_allowed_h = f"(ih*{h_ratio}*1.5)"
            
            # Final crop height: bounded by max_allowed_h, but safely above min_allowed_h
            crop_h = f"max({min_allowed_h}\\, min({target_crop_h}\\, {max_allowed_h}))"
            
            # We explicitly set crop_w based on crop_h to guarantee the exact same aspect ratio,
            # preventing scale2ref from squishing the image!
            crop_w = f"({crop_h}*{bot_aspect})"
        else:
            crop_w = "ih*(9/16)"
            crop_h = "ih*0.35"
            
        face_x = f"max(0\\,min(iw-{crop_w}\\,iw*{x_ratio}-{crop_w}/2))"
        face_y = f"max(0\\,min(ih-{crop_h}\\,ih*{y_ratio}-{crop_h}/2))"
        bottom_crop = f"crop={crop_w}:{crop_h}:{face_x}:{face_y}"
        
        filter_complex = (
            f"[0:v]{top_crop}[top];"
            f"[0:v]{bottom_crop}[bot_raw];"
            # scale bot_raw to the same width as top, but adjust height to exactly 35/65 of the top's height
            f"[bot_raw][top]scale2ref=w=iw:h=ih*(0.35/0.65)[bottom][top_ref];"
            f"[top_ref][bottom]vstack=inputs=2[stacked]"
        )
    elif layout_mode == "center":
        # Blurred background + 16:9 video perfectly centered
        filter_complex = (
            f"[0:v]split=2[bg_src][fg_src];"
            f"[bg_src]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:20[bg];"
            f"[fg_src]scale=1080:-1[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[stacked]"
        )
    else:
        # Standard 9:16 crop (Full height)
        # Tracks x_ratio, but full height (so y is always 0)
        face_x = f"max(0\\,min(iw-ih*(9/16)\\,iw*{x_ratio}-ih*(9/16)/2))"
        filter_complex = f"[0:v]crop=ih*(9/16):ih:{face_x}:0[stacked]"

    if layout_mode != "center":
        # Scale to 1080x1920 standard shorts resolution (except for center which already sets canvas to 1080x1920)
        filter_complex += ";[stacked]scale=1080:1920:flags=lanczos[scaled]"
    else:
        # Just pass stacked to scaled
        filter_complex += ";[stacked]copy[scaled]"

    # Burn captions if transcript is present
    if transcript_json_path:
        # Map color string to ASS hex BGR
        color_map = {
            "white": "&H00FFFFFF",
            "yellow": "&H0000FFFF",
            "green": "&H0000FF00",
            "cyan": "&H00FFFF00"
        }
        ass_color = color_map.get(caption_color, "&H00FFFFFF")
        
        ass_path = output_path.replace(".mp4", ".ass")
        has_ass = generate_ass_subtitles(transcript_json_path, start, end, ass_path, animation=caption_animation, color=ass_color)
        if has_ass:
            escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
            # Overlay ASS subtitles on the [scaled] stream
            # No force_style needed because the style is fully defined in the ASS header
            filter_complex += f";[scaled]subtitles='{escaped_ass}'[outv]"
        else:
            filter_complex += ";[scaled]copy[outv]"
    else:
        filter_complex += ";[scaled]copy[outv]"

    # Adjust encoding parameters based on requested quality
    preset = "medium"
    crf = "18"
    audio_bitrate = "192k"
    
    if quality == "medium":
        preset = "fast"
        crf = "23"
        audio_bitrate = "128k"
    elif quality == "low":
        preset = "veryfast"
        crf = "28"
        audio_bitrate = "96k"

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start),
        "-t", str(duration),
        "-i", video_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", crf,
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        output_path
    ]

    print(f"[Render] Rendering split-screen clip ({start}s -> {end}s): {output_path}...")
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"[Render] Completed: {output_path}")
        return os.path.abspath(output_path)
    except subprocess.CalledProcessError as e:
        print(f"[Error] ffmpeg rendering failed: {e.stderr}", file=sys.stderr)
        raise e

def render_clips_from_list(video_path: str, clips: list, output_dir: str = "generator/output", transcript_json_path: str = None, layout_mode: str = "visual_split", quality: str = "high", caption_color: str = "white", caption_animation: str = "none") -> list:
    """
    Renders multiple candidate clips from a list.
    Returns list of rendered clip file details.
    """
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # Import face tracking here to avoid circular imports if any, and only load OpenCV when needed
    try:
        from generator.visual_based.face_tracking import get_focal_point_ratios, get_dynamic_focal_ratios
    except ImportError:
        def get_focal_point_ratios(v, s, e): return (0.5, 0.5)
        def get_dynamic_focal_ratios(v, s, e, chunk_size=1.0): return [{"start":s, "end":e, "x_ratio":0.5, "y_ratio":0.5}]

    rendered_clips = []
    for idx, clip in enumerate(clips, start=1):
        start = clip["start"]
        end = clip["end"]
        reason = clip.get("reason", "Clip selection")
        title = clip.get("title", f"Short {idx}")
        
        out_filename = f"{base_name}_short_{idx}.mp4"
        out_path = os.path.join(output_dir, out_filename)

        # Get face coordinates dynamically
        dynamic_ratios = None
        if layout_mode == "vlog":
            dynamic_ratios = get_dynamic_focal_ratios(video_path, start, end, chunk_size=1.0)
            x_ratio, y_ratio = 0.5, 0.5
            w_ratio, h_ratio = 0.0, 0.0
        else:
            focal_data = get_focal_point_ratios(video_path, start, end)
            x_ratio = focal_data[0]
            y_ratio = focal_data[1]
            w_ratio = focal_data[2] if len(focal_data) > 2 else 0.0
            h_ratio = focal_data[3] if len(focal_data) > 2 else 0.0

        rendered_path = render_clip(
            video_path, start, end, out_path, 
            transcript_json_path=transcript_json_path,
            x_ratio=x_ratio, y_ratio=y_ratio,
            w_ratio=w_ratio, h_ratio=h_ratio,
            layout_mode=layout_mode,
            quality=quality,
            dynamic_ratios=dynamic_ratios,
            caption_color=caption_color,
            caption_animation=caption_animation
        )
        
        rendered_clips.append({
            "clip_number": idx,
            "start": start,
            "end": end,
            "reason": reason,
            "title": title,
            "description": clip.get("description", ""),
            "hashtags": clip.get("hashtags", ""),
            "virality_score": clip.get("virality_score", round(9.5 - idx * 0.4, 1)),
            "file_path": rendered_path
        })

    return rendered_clips

def main():
    parser = argparse.ArgumentParser(description="Render candidate 9:16 vertical short clips using ffmpeg.")
    parser.add_argument("video_path", help="Path to raw mp4 file")
    parser.add_argument("clips_json", help="Path to clips JSON array or JSON string")
    parser.add_argument("--output-dir", default="generator/output", help="Output directory for rendered clips")

    args = parser.parse_args()
    try:
        if os.path.exists(args.clips_json):
            with open(args.clips_json, "r", encoding="utf-8") as f:
                clips = json.load(f)
        else:
            clips = json.loads(args.clips_json)

        rendered = render_clips_from_list(args.video_path, clips, args.output_dir)
        print(json.dumps(rendered, indent=2))
    except Exception as e:
        print(f"[Error] Render process failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
