#!/usr/bin/env python3
"""ElevenLabs Flash v2.5 TTS script for Cursor hook notifications.

Adapted from disler/claude-code-hooks-multi-agent-observability.
Uses ElevenLabs Flash v2.5 for ultra-low latency (~75ms) text-to-speech.
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main() -> None:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("ELEVENLABS_API_KEY not found in environment", file=sys.stderr)
        sys.exit(0)

    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs.play import play
    except ImportError:
        print("elevenlabs package not installed", file=sys.stderr)
        sys.exit(0)

    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "The first move is what sets everything in motion."

    try:
        client = ElevenLabs(api_key=api_key)
        audio = client.text_to_speech.convert(
            text=text,
            voice_id="WejK3H1m7MI9CHnIjW9K",
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",
        )
        play(audio)
    except Exception as e:
        print(f"ElevenLabs TTS error: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
