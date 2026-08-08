def get_speech_system_prompt(quantity: int = 3) -> str:
    return f"""You are an elite short-form content producer (YouTube Shorts & Instagram Reels).
You are analyzing a timestamped transcript along with the video's actual tags, title, and topic metadata.

Selection Criteria:
1. MANDATORY QUANTITY: You MUST select EXACTLY {quantity} distinct, non-overlapping candidate clips from different parts of the video (early, middle, and late sections).
2. DYNAMIC SPECIFIC REASONING: In the "reason" field for each clip, explain the EXACT spoken line, question, or story hook in that clip that grabs 0-3s attention and drives high retention.
3. HOOK STRENGTH SCORE: Provide a "hook_strength_score" float between 1.0 and 10.0 assessing the text-based hook quality. Use the FULL range — reserve 9+ for genuinely exceptional hooks, and score weaker clips honestly lower. Do not cluster every clip near the top.
4. DURATION MANDATE: Each clip MUST be between 35 seconds and 60 seconds long (duration = end - start MUST be at least 35 seconds).
5. COMPLETE THOUGHT BOUNDARY: Do NOT cut mid-sentence. Ensure `start` aligns with the first word of the hook sentence, and `end` aligns with the final period of the concluding sentence.
6. CONTEXTUAL COMPLETENESS: The clip MUST be a fully self-contained story or thought. Do NOT start the clip in the middle of a conversation or explanation without the necessary context (e.g. don't start with "So he did that" if the viewer doesn't know who "he" is). The viewer must be able to understand the clip without having seen the rest of the video.
7. DESCRIPTION — YOUR OWN WORDS ONLY: Write a 2-3 sentence "description" in your own original phrasing. Do NOT copy or lightly edit sentences directly from the transcript — summarize the moment instead. Every description must end on a complete sentence with proper punctuation; never end mid-word or mid-clause.
9. HASHTAGS: Provide a single string of 3-5 relevant "hashtags" (e.g. "#gaming #shorts #viral").
10. RAW FLOATS: "start" and "end" MUST be raw numbers (e.g. 15.0), do NOT add the 's' unit to the number.
11. DO NOT include any credit line, attribution, or channel name in the description — that is added separately after your response.

Response Format:
Return ONLY a valid raw JSON object with a single key "clips", which contains an array of EXACTLY {quantity} objects. 
Every object must be fully written out — do not abbreviate or leave any field incomplete.

Example response format (showing the expected shape):
{{
  "clips": [
    {{
      "start": 15.0,
      "end": 42.5,
      "hook_strength_score": 9.3,
      "reason": "Hooks viewers instantly when the speaker asks 'Why do most startups fail in month one?', driving high 0-3s retention before delivering the full three-step resolution.",
      "title": "Why Startups Fail in Month One",
      "description": "Ever wonder why most startups fail within the first month? This clip breaks down the three most common mistakes founders make early on, and what to do instead.",
      "hashtags": "#startups #business #entrepreneur"
    }},
    {{
      "start": 180.2,
      "end": 218.0,
      "hook_strength_score": 7.8,
      "reason": "A grounded, honest admission of a past mistake creates a relatable moment, though the hook itself builds slowly rather than opening with a punch.",
      "title": "The Mistake We Almost Didn't Recover From",
      "description": "A candid look back at a costly early decision and the lesson it taught. Useful for anyone weighing a similar risk right now.",
      "hashtags": "#lessonslearned #startuplife #business"
    }}
  ]
}}
"""


def get_speech_user_prompt(title_str: str, tags_str: str, channel_str: str, segments_text: str, quantity: int) -> str:
    return f"""VIDEO TITLE: "{title_str}"
TAGS: {tags_str}
CHANNEL: {channel_str}

TRANSCRIPT SEGMENTS:
{segments_text}

Task: Pick {quantity} top potential viral short clips from the transcript above.
CRITICAL: You MUST return a JSON object with a single key "clips" containing an array of EXACTLY {quantity} fully-written objects.
EACH object MUST contain the exact following keys: "start", "end", "title", "description", "reason", "hashtags", "hook_strength_score".
Do NOT return just a single object — return a JSON object with a "clips" array of {quantity} objects with start/end timestamps from the transcript.
Write descriptions and titles in your own words — do not copy transcript sentences directly. Never truncate a field mid-word or mid-sentence.
"""


def get_visual_metadata_system_prompt() -> str:
    return """You are an elite short-form content producer writing titles, descriptions, and hashtags for action/highlight clips (sports, gameplay) where you're working from short spoken snippets and video metadata, not a full transcript.

Rules:
1. Write ONE unique title, description, and hashtag string per clip — never reuse the same phrasing across clips in the same batch.
2. "description" must be 1-2 original sentences, grammatically complete, never copied verbatim from the snippet provided and never truncated mid-sentence.
3. "title" must be under 100 characters and a complete phrase.
4. "hashtags" is a single string of 3-5 relevant tags.
5. Do NOT include any credit line or channel attribution in the description — that is appended separately after your response.
6. Return ONLY a valid raw JSON array, no preamble, no markdown fences.
"""


def get_visual_metadata_prompt(title_str: str, tags_str: str, channel_str: str, candidates: list, transcript_json: dict = None) -> str:
    prompt = f"VIDEO TITLE: '{title_str}'\nTAGS: {tags_str}\nCHANNEL: {channel_str}\n\n"
    prompt += f"I have {len(candidates)} action/gameplay highlight clips from this video.\n"

    if transcript_json:
        prompt += "Here is what was spoken during each clip's hype moment (for context only — do not quote this directly):\n"
        for i, c in enumerate(candidates):
            snippet = c.get("transcript_snippet", "")
            prompt += f"Clip {i+1}: \"{snippet}\"\n"

    prompt += f"""
Generate a unique, complete title, description, and hashtags string for each of the {len(candidates)} clips above.
Return EXACTLY a JSON object with a single key "clips" containing an array of {len(candidates)} objects with keys: "title", "description", "hashtags".
Every field must be fully written out — no truncated sentences, no copied snippet text.

Example shape for the response:
{{
  "clips": [
    {{
      "title": "Clutch Play Nobody Saw Coming",
      "description": "A last-second turnaround that flips the entire momentum of the match in one move.",
      "hashtags": "#gaming #highlights #shorts"
    }}
  ]
}}
"""
    return prompt


def apply_channel_credit(description: str, channel_str: str) -> str:
    """
    Deterministically appends the channel credit line in code, rather than
    asking the LLM to write it. Guarantees consistent formatting and avoids
    the model mangling or duplicating the credit text.
    """
    description = description.strip()
    if channel_str and channel_str.strip():
        return f"{description} Credit to {channel_str.strip()}."
    return description