#!/usr/bin/env python3
"""Offline TTS script using pyttsx3 for Cursor hook notifications.

Adapted from disler/claude-code-hooks-multi-agent-observability.
No API key required — uses system speech synthesis.
"""

import random
import sys


def main() -> None:
    try:
        import pyttsx3
    except ImportError:
        print("pyttsx3 package not installed", file=sys.stderr)
        sys.exit(0)

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 180)
        engine.setProperty("volume", 0.8)

        if len(sys.argv) > 1:
            text = " ".join(sys.argv[1:])
        else:
            text = random.choice([
                "Work complete!",
                "All done!",
                "Task finished!",
                "Job complete!",
                "Ready for next task!",
            ])

        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"pyttsx3 TTS error: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
