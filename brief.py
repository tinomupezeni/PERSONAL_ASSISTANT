#!/usr/bin/env python3
"""
CEO Brief Generator - Executive Accountability System.

Compares commitments against observed behavior.
Issues directives, not suggestions.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

try:
    from groq import Groq
except ImportError:
    print("Install groq: pip install groq")
    exit(1)

from github_activity import get_github_activity
from local_docs import scan_local_documents
from activity_monitor import get_activity_context
from commitments import (
    load_yesterday_commitment,
    load_today_commitment,
    get_commitment_context
)

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "briefs"
PROMPT_FILE = BASE_DIR / "prompts" / "ceo_brief.txt"
CONFIG_FILE = BASE_DIR / "config.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"document_directories": [], "scan_days": 7}


def get_recent_briefs(days: int = 7) -> list[dict]:
    """Load recent briefs for pattern detection."""
    briefs = []
    for file in sorted(DATA_DIR.glob("*.json"), reverse=True)[:days]:
        try:
            briefs.append(json.loads(file.read_text()))
        except Exception:
            continue
    return briefs


def load_prompt_template() -> str:
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text()
    return ""


def ask_reflection_questions() -> dict:
    """Collect daily reflection inputs."""
    print("\n" + "=" * 50)
    print("  DAILY DEBRIEF")
    print("=" * 50 + "\n")

    questions = {
        "progress": "What was accomplished today?\n> ",
        "resistance": "What was avoided or difficult?\n> ",
        "tomorrow": "Primary objective for tomorrow?\n> ",
    }

    answers = {}
    for key, prompt in questions.items():
        print(prompt, end="")
        answers[key] = input().strip()
        print()

    return answers


def get_observed_data() -> str:
    """Gather all observed data from PC."""
    sections = []

    # GitHub
    if os.environ.get("GITHUB_TOKEN"):
        gh = get_github_activity(days=1)
        if gh.get("count", 0) > 0:
            sections.append(f"GITHUB COMMITS (24h):\n{gh['summary']}")
        else:
            sections.append("GITHUB COMMITS (24h): None")

    # Documents
    config = load_config()
    dirs = config.get("document_directories", [])
    if dirs:
        docs = scan_local_documents(dirs, days=7)
        if docs.get("count", 0) > 0:
            sections.append(f"DOCUMENTS MODIFIED (7d):\n{docs['summary']}")

    # Activity
    activity = get_activity_context()
    if activity:
        sections.append(activity)

    return "\n\n".join(sections) if sections else "No observed data available."


def get_commitment_data() -> str:
    """Get commitment context for gap analysis."""
    yesterday = load_yesterday_commitment()
    today = load_today_commitment()

    lines = []

    if yesterday:
        lines.append("YESTERDAY'S COMMITMENT:")
        lines.append(f"  Action: {yesterday.get('commitment', 'None')}")
        lines.append(f"  Success Metric: {yesterday.get('success_metric', 'None')}")
        lines.append(f"  Expected Obstacle: {yesterday.get('expected_obstacle', 'None')}")
    else:
        lines.append("YESTERDAY'S COMMITMENT: None recorded")

    if today:
        lines.append(f"\nTODAY'S COMMITMENT: {today.get('commitment', 'None')}")

    return "\n".join(lines)


def get_pattern_data(recent_briefs: list[dict]) -> str:
    """Extract patterns from recent briefs."""
    if not recent_briefs:
        return ""

    lines = ["PATTERNS (last 7 days):"]
    for brief in recent_briefs[:5]:
        date = brief.get("date", "unknown")
        resistance = brief.get("answers", {}).get("resistance", "")
        if resistance:
            lines.append(f"  - {date}: Avoided: {resistance}")

    return "\n".join(lines)


# JARVIS-style system prompt
SYSTEM_PROMPT = """You are an executive AI system generating a daily accountability brief.

TONE:
- Calm, factual, executive
- No praise, no encouragement, no emotional language
- State observations, not interpretations
- Issue directives, not suggestions

RULES:
- Maximum 250 words
- Compare COMMITMENT against OBSERVED DATA
- If commitment was not fulfilled, state the gap neutrally
- Do not speculate on reasons unless data supports it

OUTPUT FORMAT (follow exactly):

COMMITMENT REVIEW:
[Compare yesterday's commitment against observed behavior. State if fulfilled or not. One sentence.]

MOMENTUM:
[What moved forward. Facts only.]

RISK:
[What needs attention. Facts only.]

PATTERN:
[Recurring behavior if detected. Otherwise: "No pattern detected."]

CEO DIRECTIVE:
[Exactly ONE specific, measurable action for tomorrow. No motivation. No options. Just the directive.]
"""


def generate_brief(answers: dict, recent_briefs: list[dict]) -> str:
    """Generate CEO brief with gap analysis."""
    client = Groq()

    # Gather all context
    observed_data = get_observed_data()
    commitment_data = get_commitment_data()
    pattern_data = get_pattern_data(recent_briefs)

    user_prompt = f"""Generate the CEO Brief.

DATE: {datetime.now().strftime("%Y-%m-%d")}

USER DEBRIEF:
- Accomplished: {answers.get('progress', 'Not provided')}
- Avoided: {answers.get('resistance', 'Not provided')}
- Tomorrow's intent: {answers.get('tomorrow', 'Not provided')}

{commitment_data}

OBSERVED DATA:
{observed_data}

{pattern_data}

Generate the brief following the exact format specified. End with a CEO DIRECTIVE."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=600,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content


def save_brief(answers: dict, brief: str, commitment_data: str = "") -> Path:
    """Save brief to history."""
    today = datetime.now()
    filename = today.strftime("%Y-%m-%d") + ".json"
    filepath = DATA_DIR / filename

    data = {
        "date": today.strftime("%Y-%m-%d"),
        "timestamp": today.isoformat(),
        "answers": answers,
        "brief": brief,
        "commitment_reviewed": load_yesterday_commitment()
    }

    filepath.write_text(json.dumps(data, indent=2))
    return filepath


def display_brief(brief: str):
    """Display the generated brief."""
    print("\n" + "=" * 50)
    print("  CEO BRIEF - " + datetime.now().strftime("%Y-%m-%d"))
    print("=" * 50 + "\n")
    print(brief)
    print("\n" + "=" * 50 + "\n")


def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY not set")
        exit(1)

    # CLI args or interactive
    if len(sys.argv) == 4:
        answers = {
            "progress": sys.argv[1],
            "resistance": sys.argv[2],
            "tomorrow": sys.argv[3]
        }
    else:
        answers = ask_reflection_questions()

    if not any(answers.values()):
        print("No input. Exiting.")
        return

    print("Generating brief...")

    recent = get_recent_briefs(7)
    brief = generate_brief(answers, recent)

    filepath = save_brief(answers, brief)

    display_brief(brief)
    print(f"Saved: {filepath.name}")


if __name__ == "__main__":
    main()
