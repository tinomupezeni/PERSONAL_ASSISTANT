"""
GitHub Sync Module for Ada.

Automatically pushes code and memory to GitHub repository.
Keeps a backup of Ada's state and enables cross-device sync.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
REPO_URL = "https://github.com/tinomupezeni/PERSONAL_ASSISTANT.git"


def run_git(command: str) -> tuple[bool, str]:
    """Run a git command and return success status and output."""
    try:
        result = subprocess.run(
            f"git {command}",
            shell=True,
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output.strip()
    except Exception as e:
        return False, str(e)


def get_status() -> dict:
    """Get current git status."""
    success, output = run_git("status --porcelain")

    if not success:
        return {"error": output}

    changes = {
        "modified": [],
        "added": [],
        "deleted": [],
        "untracked": []
    }

    for line in output.split("\n"):
        if not line.strip():
            continue
        status = line[:2]
        file = line[3:]

        if status.startswith("M") or status.endswith("M"):
            changes["modified"].append(file)
        elif status.startswith("A"):
            changes["added"].append(file)
        elif status.startswith("D"):
            changes["deleted"].append(file)
        elif status.startswith("?"):
            changes["untracked"].append(file)

    return changes


def sync_to_github(message: str = None) -> dict:
    """
    Sync all changes to GitHub.

    Steps:
    1. Add all changes
    2. Commit with timestamp
    3. Push to origin
    """
    results = {
        "success": False,
        "steps": [],
        "timestamp": datetime.now().isoformat()
    }

    # Check for changes
    status = get_status()
    if "error" in status:
        results["error"] = status["error"]
        return results

    total_changes = sum(len(v) for v in status.values())
    if total_changes == 0:
        results["message"] = "No changes to sync"
        results["success"] = True
        return results

    results["changes"] = status

    # Add all changes
    success, output = run_git("add -A")
    results["steps"].append({
        "action": "git add -A",
        "success": success,
        "output": output
    })

    if not success:
        results["error"] = "Failed to stage changes"
        return results

    # Create commit message
    if not message:
        message = f"Ada auto-sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Add summary of changes
        parts = []
        if status["modified"]:
            parts.append(f"{len(status['modified'])} modified")
        if status["added"]:
            parts.append(f"{len(status['added'])} added")
        if status["untracked"]:
            parts.append(f"{len(status['untracked'])} new")

        if parts:
            message += f" ({', '.join(parts)})"

    # Commit
    success, output = run_git(f'commit -m "{message}"')
    results["steps"].append({
        "action": "git commit",
        "success": success,
        "output": output
    })

    if not success and "nothing to commit" not in output.lower():
        results["error"] = "Failed to commit"
        return results

    # Push
    success, output = run_git("push origin main")

    # Try 'master' if 'main' fails
    if not success and "master" in output.lower():
        success, output = run_git("push origin master")

    results["steps"].append({
        "action": "git push",
        "success": success,
        "output": output
    })

    if not success:
        # Check if we need to set upstream
        if "no upstream" in output.lower() or "set-upstream" in output.lower():
            success, output = run_git("push -u origin main")
            if not success:
                success, output = run_git("push -u origin master")
            results["steps"].append({
                "action": "git push -u",
                "success": success,
                "output": output
            })

    results["success"] = success
    if success:
        results["message"] = f"Synced {total_changes} changes to GitHub"
    else:
        results["error"] = output

    return results


def pull_from_github() -> dict:
    """Pull latest changes from GitHub."""
    results = {
        "success": False,
        "timestamp": datetime.now().isoformat()
    }

    success, output = run_git("pull origin main")

    if not success:
        success, output = run_git("pull origin master")

    results["success"] = success
    results["output"] = output

    if success:
        results["message"] = "Pulled latest changes"
    else:
        results["error"] = output

    return results


def get_sync_status() -> str:
    """Get formatted sync status."""
    lines = ["SYNC STATUS:"]

    # Check remote
    success, remote = run_git("remote get-url origin")
    if success:
        lines.append(f"  Remote: {remote}")
    else:
        lines.append("  Remote: Not configured")

    # Check branch
    success, branch = run_git("branch --show-current")
    if success:
        lines.append(f"  Branch: {branch}")

    # Check ahead/behind
    run_git("fetch origin")  # Fetch to compare
    success, output = run_git("status -sb")
    if success and "[" in output:
        # Extract ahead/behind info
        lines.append(f"  Status: {output.split(chr(10))[0]}")

    # Local changes
    status = get_status()
    if "error" not in status:
        total = sum(len(v) for v in status.values())
        if total > 0:
            lines.append(f"  Uncommitted: {total} files")
            for category, files in status.items():
                if files:
                    lines.append(f"    {category}: {len(files)}")
        else:
            lines.append("  Working tree clean")

    return "\n".join(lines)


def setup_gitignore():
    """Ensure sensitive files are gitignored."""
    gitignore_path = BASE_DIR / ".gitignore"

    required_ignores = [
        "# Secrets",
        "credentials.json",
        "token.json",
        ".env",
        "",
        "# Python",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        "",
        "# IDE",
        ".vscode/",
        ".idea/",
        "",
        "# Data (optional - remove if you want to sync memory)",
        "# data/memory/",
        "# data/activity/",
    ]

    if gitignore_path.exists():
        existing = gitignore_path.read_text()
    else:
        existing = ""

    # Add missing entries
    added = []
    for entry in required_ignores:
        if entry and entry not in existing and not entry.startswith("#"):
            added.append(entry)

    if added:
        with open(gitignore_path, "a") as f:
            f.write("\n" + "\n".join(added))
        return f"Added to .gitignore: {', '.join(added)}"

    return "Gitignore already configured"


if __name__ == "__main__":
    print("=== Ada GitHub Sync ===\n")

    # Show status
    print(get_sync_status())
    print()

    # Sync
    print("Syncing...")
    result = sync_to_github()

    if result["success"]:
        print(f"Success: {result.get('message', 'Done')}")
    else:
        print(f"Error: {result.get('error', 'Unknown')}")
        for step in result.get("steps", []):
            print(f"  {step['action']}: {'OK' if step['success'] else 'FAIL'}")
