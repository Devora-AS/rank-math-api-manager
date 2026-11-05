#!/usr/bin/env python3
"""Anthropic LLM helper for Cursor hook scripts.

Adapted from disler/claude-code-hooks-multi-agent-observability.
Uses claude-haiku-4-5-20251001 for fast, efficient prompting.
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def prompt_llm(prompt_text: str) -> str | None:
    """Send a prompt to Anthropic's fastest model and return the response text."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt_text}],
        )
        return message.content[0].text.strip()
    except Exception:
        return None


def generate_completion_message() -> str | None:
    """Generate a short, friendly completion message via Anthropic."""
    engineer_name = os.getenv("ENGINEER_NAME", "").strip()

    if engineer_name:
        name_instruction = (
            f"Sometimes (about 30% of the time) include the engineer's name "
            f"'{engineer_name}' in a natural way."
        )
        examples = (
            f'Examples of the style:\n'
            f'- Standard: "Work complete!", "All done!", "Task finished!", "Ready for your next move!"\n'
            f'- Personalized: "{engineer_name}, all set!", "Ready for you, {engineer_name}!"'
        )
    else:
        name_instruction = ""
        examples = 'Examples of the style: "Work complete!", "All done!", "Task finished!", "Ready for your next move!"'

    prompt = f"""Generate a short, concise, friendly completion message for when an AI coding assistant finishes a task.

Requirements:
- Keep it under 10 words
- Make it positive and future focused
- Use natural, conversational language
- Focus on completion/readiness
- Do NOT include quotes, formatting, or explanations
- Return ONLY the completion message text
{name_instruction}

{examples}

Generate ONE completion message:"""

    response = prompt_llm(prompt)

    if response:
        response = response.strip().strip('"').strip("'").strip()
        response = response.split("\n")[0].strip()

    return response


def generate_agent_name() -> str | None:
    """Generate a single-word creative agent name via Anthropic."""
    prompt = """Generate a single creative agent name for an AI coding assistant.

Requirements:
- MUST be a single word (no spaces)
- MUST be alphanumeric only (letters and numbers, no special characters)
- Make it memorable and related to coding/tech/AI
- Keep it between 4-12 characters
- Examples: CodeNinja, ByteBot, PixelPro, NexusAI, SwiftDev
- Do NOT include quotes, formatting, or explanations
- Return ONLY the agent name

Generate ONE agent name:"""

    response = prompt_llm(prompt)

    if response:
        response = response.strip().strip('"').strip("'").strip()
        response = response.split()[0] if response else None
        if response and response.isalnum():
            return response

    return None


def main() -> None:
    """Command line interface for testing."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--completion":
            message = generate_completion_message()
            print(message if message else "Error generating completion message")
        elif sys.argv[1] == "--agent-name":
            agent_name = generate_agent_name()
            print(agent_name if agent_name else "Error generating agent name")
        else:
            prompt_text = " ".join(sys.argv[1:])
            response = prompt_llm(prompt_text)
            print(response if response else "Error calling Anthropic API")
    else:
        print(
            "Usage: ./anth.py 'your prompt here' or ./anth.py --completion or ./anth.py --agent-name"
        )


if __name__ == "__main__":
    main()
