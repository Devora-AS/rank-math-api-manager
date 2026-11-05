#!/usr/bin/env python3
"""OpenAI TTS script for Cursor hook notifications.

Adapted from disler/claude-code-hooks-multi-agent-observability.
Uses gpt-4o-mini-tts with nova voice and streaming via LocalAudioPlayer.
"""

import asyncio
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


async def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found in environment", file=sys.stderr)
        sys.exit(0)

    try:
        from openai import AsyncOpenAI
        from openai.helpers import LocalAudioPlayer
    except ImportError:
        print("openai package not installed (need openai[voice_helpers])", file=sys.stderr)
        sys.exit(0)

    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Today is a wonderful day to build something people love!"

    try:
        client = AsyncOpenAI(api_key=api_key)
        async with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="nova",
            input=text,
            instructions="Speak in a cheerful, positive yet professional tone.",
            response_format="mp3",
        ) as response:
            await LocalAudioPlayer().play(response)
    except Exception as e:
        print(f"OpenAI TTS error: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
