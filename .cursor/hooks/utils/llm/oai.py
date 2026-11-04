#!/usr/bin/env python3
"""OpenAI LLM helper for Cursor hook scripts.

Adapted from disler/claude-code-hooks-multi-agent-observability.
Uses gpt-4.1-nano for fast, efficient prompting.
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def prompt_llm(prompt_text: str) -> str | None:
    """Send a prompt to OpenAI's fastest model and return the response text."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt_text}],
            max_tokens=100,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def generate_completion_message() -> str | None:
    """Generate a short, friendly completion message via OpenAI."""
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

    prompt = f"""Generate a short, friendly completion message for when an AI coding assistant finishes a task.

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


def main() -> None:
    """Command line interface for testing."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--completion":
            message = generate_completion_message()
            print(message if message else "Error generating completion message")
        else:
            prompt_text = " ".join(sys.argv[1:])
            response = prompt_llm(prompt_text)
            print(response if response else "Error calling OpenAI API")
    else:
        print("Usage: ./oai.py 'your prompt here' or ./oai.py --completion")


if __name__ == "__main__":
    main()
