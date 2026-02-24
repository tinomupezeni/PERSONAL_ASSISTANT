"""
Memory & Learning System for Ada.

Ada learns about you over time. Remembers your goals, patterns, preferences.
This is what makes her YOUR assistant, not just AN assistant.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any

try:
    from groq import Groq
except ImportError:
    Groq = None

BASE_DIR = Path(__file__).parent
MEMORY_DIR = BASE_DIR / "data" / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# Core memory files
PROFILE_FILE = MEMORY_DIR / "profile.json"
PATTERNS_FILE = MEMORY_DIR / "patterns.json"
FACTS_FILE = MEMORY_DIR / "facts.json"
INSIGHTS_FILE = MEMORY_DIR / "insights.json"


# ============================================================
# PROFILE - Who you are
# ============================================================

def get_profile() -> dict:
    """Get user profile."""
    if PROFILE_FILE.exists():
        return json.loads(PROFILE_FILE.read_text())
    return {
        "name": "",
        "role": "",
        "primary_goals": [],
        "active_projects": [],
        "working_hours": {"start": "09:00", "end": "18:00"},
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat()
    }


def update_profile(updates: dict) -> dict:
    """Update user profile."""
    profile = get_profile()
    profile.update(updates)
    profile["last_updated"] = datetime.now().isoformat()
    PROFILE_FILE.write_text(json.dumps(profile, indent=2))
    return profile


def set_name(name: str):
    """Set user's name."""
    return update_profile({"name": name})


def add_goal(goal: str):
    """Add a primary goal."""
    profile = get_profile()
    if goal not in profile["primary_goals"]:
        profile["primary_goals"].append(goal)
    return update_profile(profile)


def add_project(project: str):
    """Add an active project."""
    profile = get_profile()
    if project not in profile["active_projects"]:
        profile["active_projects"].append(project)
    return update_profile(profile)


def remove_goal(goal: str):
    """Remove a goal."""
    profile = get_profile()
    profile["primary_goals"] = [g for g in profile["primary_goals"] if g.lower() != goal.lower()]
    return update_profile(profile)


def remove_project(project: str):
    """Remove a project."""
    profile = get_profile()
    profile["active_projects"] = [p for p in profile["active_projects"] if p.lower() != project.lower()]
    return update_profile(profile)


# ============================================================
# FACTS - What Ada knows about you
# ============================================================

def get_facts() -> dict:
    """Get stored facts."""
    if FACTS_FILE.exists():
        return json.loads(FACTS_FILE.read_text())
    return {"facts": [], "last_updated": datetime.now().isoformat()}


def add_fact(fact: str, category: str = "general"):
    """Store a fact about the user."""
    data = get_facts()
    data["facts"].append({
        "fact": fact,
        "category": category,
        "added_at": datetime.now().isoformat()
    })
    data["last_updated"] = datetime.now().isoformat()
    FACTS_FILE.write_text(json.dumps(data, indent=2))
    return data


def get_facts_by_category(category: str) -> list[str]:
    """Get facts by category."""
    data = get_facts()
    return [f["fact"] for f in data["facts"] if f.get("category") == category]


# ============================================================
# PATTERNS - What Ada has learned about your behavior
# ============================================================

def get_patterns() -> dict:
    """Get learned patterns."""
    if PATTERNS_FILE.exists():
        return json.loads(PATTERNS_FILE.read_text())
    return {
        "avoidance_patterns": [],      # Things you tend to avoid
        "productivity_patterns": [],   # When/how you're productive
        "distraction_triggers": [],    # What distracts you
        "success_patterns": [],        # What leads to success
        "last_updated": datetime.now().isoformat()
    }


def add_pattern(pattern: str, pattern_type: str):
    """Add a learned pattern."""
    data = get_patterns()

    if pattern_type not in data:
        data[pattern_type] = []

    # Don't duplicate
    existing = [p["pattern"] if isinstance(p, dict) else p for p in data[pattern_type]]
    if pattern.lower() not in [e.lower() for e in existing]:
        data[pattern_type].append({
            "pattern": pattern,
            "observed_at": datetime.now().isoformat(),
            "confidence": 1
        })

    data["last_updated"] = datetime.now().isoformat()
    PATTERNS_FILE.write_text(json.dumps(data, indent=2))
    return data


def increment_pattern_confidence(pattern: str, pattern_type: str):
    """Increase confidence when pattern is observed again."""
    data = get_patterns()

    if pattern_type in data:
        for p in data[pattern_type]:
            if isinstance(p, dict) and p.get("pattern", "").lower() == pattern.lower():
                p["confidence"] = p.get("confidence", 1) + 1
                p["last_observed"] = datetime.now().isoformat()

    data["last_updated"] = datetime.now().isoformat()
    PATTERNS_FILE.write_text(json.dumps(data, indent=2))
    return data


# ============================================================
# INSIGHTS - What Ada has inferred
# ============================================================

def get_insights() -> dict:
    """Get Ada's insights about you."""
    if INSIGHTS_FILE.exists():
        return json.loads(INSIGHTS_FILE.read_text())
    return {
        "insights": [],
        "last_updated": datetime.now().isoformat()
    }


def add_insight(insight: str, evidence: str = ""):
    """Add an insight Ada has learned."""
    data = get_insights()
    data["insights"].append({
        "insight": insight,
        "evidence": evidence,
        "generated_at": datetime.now().isoformat()
    })
    data["last_updated"] = datetime.now().isoformat()
    INSIGHTS_FILE.write_text(json.dumps(data, indent=2))
    return data


# ============================================================
# LEARNING - Ada learns from interactions
# ============================================================

def learn_from_brief(brief_data: dict):
    """
    Learn from a CEO brief.

    Extracts patterns from resistance, successes, etc.
    """
    answers = brief_data.get("answers", {})

    # Learn avoidance pattern
    resistance = answers.get("resistance", "")
    if resistance:
        add_pattern(resistance, "avoidance_patterns")

    # Learn from commitment data
    commitment = brief_data.get("commitment_reviewed")
    if commitment:
        obstacle = commitment.get("expected_obstacle", "")
        if obstacle:
            add_pattern(obstacle, "distraction_triggers")


def learn_from_conversation(user_message: str, context: str = ""):
    """
    Learn from conversation.

    Extracts facts, preferences, goals mentioned.
    """
    # This would ideally use LLM to extract information
    # For now, look for explicit patterns

    message_lower = user_message.lower()

    # Detect goal mentions
    if "my goal is" in message_lower or "i want to" in message_lower:
        # Could extract and store
        pass

    # Detect project mentions
    if "working on" in message_lower or "my project" in message_lower:
        pass


def analyze_and_learn(days: int = 7):
    """
    Analyze recent briefs and learn patterns.

    Run periodically to update Ada's understanding.
    """
    from brief import get_recent_briefs

    briefs = get_recent_briefs(days)

    # Count avoidance topics
    avoidance_counts = {}
    for brief in briefs:
        resistance = brief.get("answers", {}).get("resistance", "")
        if resistance:
            key = resistance.lower()[:50]  # Normalize
            avoidance_counts[key] = avoidance_counts.get(key, 0) + 1

    # Add patterns with confidence based on frequency
    for pattern, count in avoidance_counts.items():
        if count >= 2:  # Appeared at least twice
            add_pattern(
                f"Recurring avoidance: {pattern}",
                "avoidance_patterns"
            )

    return avoidance_counts


# ============================================================
# MEMORY CONTEXT - What Ada includes in prompts
# ============================================================

def get_memory_context() -> str:
    """
    Get formatted memory context for LLM prompts.

    This is what makes Ada personalized.
    """
    profile = get_profile()
    patterns = get_patterns()
    facts = get_facts()
    insights = get_insights()

    lines = ["USER MEMORY:"]

    # Profile
    if profile.get("name"):
        lines.append(f"Name: {profile['name']}")
    if profile.get("role"):
        lines.append(f"Role: {profile['role']}")
    if profile.get("primary_goals"):
        lines.append(f"Goals: {', '.join(profile['primary_goals'])}")
    if profile.get("active_projects"):
        lines.append(f"Projects: {', '.join(profile['active_projects'])}")

    # Key facts
    fact_list = facts.get("facts", [])
    if fact_list:
        lines.append("\nKnown Facts:")
        for f in fact_list[-5:]:  # Last 5 facts
            lines.append(f"  - {f['fact']}")

    # Patterns
    avoidance = patterns.get("avoidance_patterns", [])
    if avoidance:
        lines.append("\nAvoidance Patterns:")
        for p in avoidance[-3:]:  # Top 3
            pattern = p["pattern"] if isinstance(p, dict) else p
            lines.append(f"  - {pattern}")

    distractions = patterns.get("distraction_triggers", [])
    if distractions:
        lines.append("\nDistraction Triggers:")
        for d in distractions[-3:]:
            trigger = d["pattern"] if isinstance(d, dict) else d
            lines.append(f"  - {trigger}")

    # Insights
    insight_list = insights.get("insights", [])
    if insight_list:
        lines.append("\nInsights:")
        for i in insight_list[-3:]:
            lines.append(f"  - {i['insight']}")

    return "\n".join(lines) if len(lines) > 1 else ""


def get_profile_summary() -> str:
    """Get a brief profile summary."""
    profile = get_profile()

    parts = []
    if profile.get("name"):
        parts.append(f"User: {profile['name']}")
    if profile.get("primary_goals"):
        parts.append(f"Goals: {', '.join(profile['primary_goals'][:3])}")
    if profile.get("active_projects"):
        parts.append(f"Projects: {', '.join(profile['active_projects'][:3])}")

    return " | ".join(parts) if parts else "No profile data yet."


# ============================================================
# INTERACTIVE LEARNING
# ============================================================

def run_learning_session():
    """
    Interactive session where Ada asks questions to learn about you.
    """
    print("\n" + "=" * 50)
    print("  LEARNING SESSION")
    print("  Ada will ask questions to learn about you.")
    print("=" * 50 + "\n")

    # Name
    name = input("What should I call you?\n> ").strip()
    if name:
        set_name(name)

    # Role
    role = input("\nWhat is your primary role? (e.g., Software Engineer, Student, Founder)\n> ").strip()
    if role:
        update_profile({"role": role})

    # Goals
    print("\nWhat are your primary goals? (Enter each goal, empty line to finish)")
    while True:
        goal = input("> ").strip()
        if not goal:
            break
        add_goal(goal)

    # Projects
    print("\nWhat projects are you actively working on? (Enter each, empty line to finish)")
    while True:
        project = input("> ").strip()
        if not project:
            break
        add_project(project)

    # Key facts
    print("\nAny important facts I should know? (e.g., 'I work best in the morning')")
    print("Enter each fact, empty line to finish:")
    while True:
        fact = input("> ").strip()
        if not fact:
            break
        add_fact(fact, "self_reported")

    print("\n" + "=" * 50)
    print("  Learning complete. I now know:")
    print("=" * 50)
    print(get_memory_context())


if __name__ == "__main__":
    # Interactive learning session
    run_learning_session()
