"""
Commitment Engine for CEO Brief Agent.

Tracks daily commitments and compares against observed behavior.
One commitment per day. No excuses. Just data.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent
INTENTS_DIR = BASE_DIR / "data" / "intents"
INTENTS_DIR.mkdir(parents=True, exist_ok=True)


def get_intent_path(date: datetime) -> Path:
    """Get path to intent file for a given date."""
    return INTENTS_DIR / f"{date.strftime('%Y-%m-%d')}.json"


def save_commitment(
    primary_goal: str,
    commitment: str,
    success_metric: str,
    expected_obstacle: str,
    target_date: Optional[datetime] = None
) -> Path:
    """
    Save a commitment for tomorrow (or specified date).

    Only ONE commitment per day. Overwrites if exists.
    """
    if target_date is None:
        target_date = datetime.now() + timedelta(days=1)

    data = {
        "date": target_date.strftime("%Y-%m-%d"),
        "primary_goal": primary_goal.strip(),
        "commitment": commitment.strip(),
        "success_metric": success_metric.strip(),
        "expected_obstacle": expected_obstacle.strip(),
        "created_at": datetime.now().isoformat()
    }

    filepath = get_intent_path(target_date)
    filepath.write_text(json.dumps(data, indent=2))
    return filepath


def load_commitment(date: Optional[datetime] = None) -> Optional[dict]:
    """Load commitment for a given date. Defaults to today."""
    if date is None:
        date = datetime.now()

    filepath = get_intent_path(date)

    if not filepath.exists():
        return None

    try:
        return json.loads(filepath.read_text())
    except Exception:
        return None


def load_yesterday_commitment() -> Optional[dict]:
    """Load yesterday's commitment for review."""
    yesterday = datetime.now() - timedelta(days=1)
    return load_commitment(yesterday)


def load_today_commitment() -> Optional[dict]:
    """Load today's commitment."""
    return load_commitment(datetime.now())


def get_commitment_context() -> str:
    """
    Get commitment context for CEO Brief.

    Returns formatted string with yesterday's commitment for gap analysis.
    """
    yesterday = load_yesterday_commitment()
    today = load_today_commitment()

    lines = []

    if yesterday:
        lines.append("YESTERDAY'S COMMITMENT:")
        lines.append(f"  Goal: {yesterday.get('primary_goal', 'Not set')}")
        lines.append(f"  Commitment: {yesterday.get('commitment', 'Not set')}")
        lines.append(f"  Success Metric: {yesterday.get('success_metric', 'Not set')}")
        lines.append(f"  Expected Obstacle: {yesterday.get('expected_obstacle', 'Not set')}")
    else:
        lines.append("YESTERDAY'S COMMITMENT: None recorded.")

    lines.append("")

    if today:
        lines.append("TODAY'S COMMITMENT:")
        lines.append(f"  Goal: {today.get('primary_goal', 'Not set')}")
        lines.append(f"  Commitment: {today.get('commitment', 'Not set')}")
        lines.append(f"  Success Metric: {today.get('success_metric', 'Not set')}")
    else:
        lines.append("TODAY'S COMMITMENT: None recorded. Use /commit to set.")

    return "\n".join(lines)


def list_recent_commitments(days: int = 7) -> list[dict]:
    """List recent commitments for pattern analysis."""
    commitments = []

    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        commitment = load_commitment(date)
        if commitment:
            commitments.append(commitment)

    return commitments


def analyze_commitment_patterns(days: int = 14) -> dict:
    """
    Analyze commitment patterns.

    Returns:
        - total_commitments: Number of commitments made
        - completion_rate: Based on subsequent briefs (future feature)
        - common_obstacles: Frequently mentioned obstacles
    """
    commitments = list_recent_commitments(days)

    obstacles = []
    for c in commitments:
        obstacle = c.get("expected_obstacle", "").lower()
        if obstacle:
            obstacles.append(obstacle)

    return {
        "total_commitments": len(commitments),
        "days_analyzed": days,
        "common_obstacles": obstacles[:5]  # Top 5
    }


if __name__ == "__main__":
    # Test
    print("Testing commitment system...")

    # Save a test commitment
    save_commitment(
        primary_goal="Ship SMEPulse onboarding flow",
        commitment="Complete user registration API endpoint",
        success_metric="Endpoint returns 200 with valid JWT",
        expected_obstacle="Getting distracted by UI polish"
    )

    print(get_commitment_context())
