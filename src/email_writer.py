import json
import os
from pathlib import Path

from openai import OpenAI


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT_PATH = ROOT_DIR / "prompts" / "outreach_prompt.txt"


class EmailGenerationError(Exception):
    """Raised when the AI does not return a usable email."""


def load_prompt() -> str:
    """Load the outreach instructions used by the AI."""
    prompt_path = Path(
        os.getenv("OUTREACH_PROMPT_PATH", str(DEFAULT_PROMPT_PATH))
    )

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_path}"
        )

    prompt = prompt_path.read_text(encoding="utf-8").strip()

    if not prompt:
        raise ValueError("The outreach prompt is empty.")

    return prompt


def _remove_code_fence(text: str) -> str:
    """Remove Markdown code fences if the model adds them."""
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text


def _parse_response(text: str) -> dict:
    """Convert the model response into a subject/body dictionary."""
    cleaned = _remove_code_fence(text)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise EmailGenerationError(
            "The AI response was not valid JSON."
        ) from exc

    if not isinstance(result, dict):
        raise EmailGenerationError(
            "The AI response was not a JSON object."
        )

    subject = result.get("subject")
    body = result.get("body")

    if not isinstance(subject, str) or not subject.strip():
        raise EmailGenerationError(
            "The generated email did not contain a valid subject."
        )

    if not isinstance(body, str) or not body.strip():
        raise EmailGenerationError(
            "The generated email did not contain a valid body."
        )

    return {
        "subject": subject.strip(),
        "body": body.strip()
    }


def generate_email(contact: dict) -> dict:
    """
    Generate a personalized outreach email for one contact.

    Returns:
        {
            "subject": "...",
            "body": "..."
        }
    """
    base_prompt = load_prompt()

    contact_information = {
        "name": contact.get("name", ""),
        "email": contact.get("email", ""),
        "organization": contact.get("organization", ""),
        "role": contact.get("role", ""),
        "reason": contact.get("reason", ""),
        "notes": contact.get("notes", "")
    }

    request = f"""
{base_prompt}

RECIPIENT INFORMATION

{json.dumps(contact_information, indent=2, ensure_ascii=False)}

IMPORTANT OUTPUT REQUIREMENT:

Return ONLY a JSON object in exactly this general form:

{{
  "subject": "The email subject",
  "body": "The complete plain-text email"
}}

Do not include Markdown.
Do not include explanations outside the JSON.
Do not invent information about the recipient.
If information was not provided, do not pretend to know it.
"""

    client = OpenAI()

    model = os.getenv("OPENAI_MODEL", "gpt-6-luna")

    response = client.responses.create(
        model=model,
        input=request,
        max_output_tokens=800,
        store=False
    )

    raw_output = response.output_text

    if not raw_output:
        raise EmailGenerationError(
            "The AI returned an empty response."
        )

    return _parse_response(raw_output)