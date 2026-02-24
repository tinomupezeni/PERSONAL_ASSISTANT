"""
GitHub activity tracker for CEO Brief.

Pulls recent commits across your repositories.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional


def get_github_activity(
    username: Optional[str] = None,
    token: Optional[str] = None,
    days: int = 1,
    repos: Optional[list[str]] = None
) -> dict:
    """
    Fetch recent GitHub activity.

    Args:
        username: GitHub username (optional if token has user scope)
        token: GitHub personal access token
        days: How many days back to look
        repos: Specific repos to check (format: "owner/repo"). If None, checks all.

    Returns:
        Dict with commits, summary stats
    """
    token = token or os.environ.get("GITHUB_TOKEN")

    if not token:
        return {"error": "No GitHub token provided", "commits": [], "summary": ""}

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Get username if not provided
    if not username:
        user_resp = requests.get("https://api.github.com/user", headers=headers)
        if user_resp.status_code == 200:
            username = user_resp.json().get("login")
        else:
            return {"error": "Could not fetch GitHub user", "commits": [], "summary": ""}

    since = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    all_commits = []

    if repos:
        # Check specific repos
        for repo in repos:
            commits = fetch_repo_commits(repo, username, since, headers)
            all_commits.extend(commits)
    else:
        # Get repos user has pushed to recently via events
        events_url = f"https://api.github.com/users/{username}/events"
        events_resp = requests.get(events_url, headers=headers, params={"per_page": 100})

        if events_resp.status_code == 200:
            events = events_resp.json()
            seen_repos = set()

            for event in events:
                if event.get("type") == "PushEvent":
                    repo_name = event.get("repo", {}).get("name")
                    if repo_name and repo_name not in seen_repos:
                        seen_repos.add(repo_name)
                        # Extract commits from push event
                        payload = event.get("payload", {})
                        for commit in payload.get("commits", []):
                            created_at = event.get("created_at", "")
                            if created_at >= since:
                                all_commits.append({
                                    "repo": repo_name,
                                    "message": commit.get("message", "").split("\n")[0],
                                    "sha": commit.get("sha", "")[:7],
                                    "date": created_at
                                })

    # Build summary
    summary = build_summary(all_commits)

    return {
        "commits": all_commits,
        "summary": summary,
        "count": len(all_commits)
    }


def fetch_repo_commits(repo: str, author: str, since: str, headers: dict) -> list:
    """Fetch commits from a specific repo."""
    url = f"https://api.github.com/repos/{repo}/commits"
    params = {"author": author, "since": since, "per_page": 50}

    resp = requests.get(url, headers=headers, params=params)
    commits = []

    if resp.status_code == 200:
        for c in resp.json():
            commits.append({
                "repo": repo,
                "message": c.get("commit", {}).get("message", "").split("\n")[0],
                "sha": c.get("sha", "")[:7],
                "date": c.get("commit", {}).get("author", {}).get("date", "")
            })

    return commits


def build_summary(commits: list) -> str:
    """Build a human-readable summary of commits."""
    if not commits:
        return "No commits in the last day."

    # Group by repo
    by_repo = {}
    for c in commits:
        repo = c["repo"]
        if repo not in by_repo:
            by_repo[repo] = []
        by_repo[repo].append(c["message"])

    lines = [f"{len(commits)} commits across {len(by_repo)} repos:"]
    for repo, messages in by_repo.items():
        lines.append(f"\n{repo} ({len(messages)}):")
        for msg in messages[:5]:  # Limit to 5 per repo
            lines.append(f"  - {msg[:60]}")
        if len(messages) > 5:
            lines.append(f"  - ... and {len(messages) - 5} more")

    return "\n".join(lines)


if __name__ == "__main__":
    # Test
    result = get_github_activity(days=1)
    if result.get("error"):
        print(f"Error: {result['error']}")
    else:
        print(result["summary"])
