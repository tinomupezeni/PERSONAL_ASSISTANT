"""
Activity Monitor for CEO Brief Agent.

Tracks active windows, application usage, and productivity patterns.
"""

import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Optional
import threading

try:
    import win32gui
    import win32process
    import psutil
except ImportError:
    win32gui = None
    psutil = None

# Paths
BASE_DIR = Path(__file__).parent
ACTIVITY_DIR = BASE_DIR / "data" / "activity"
ACTIVITY_DIR.mkdir(parents=True, exist_ok=True)

# Categories for apps
APP_CATEGORIES = {
    # Productive
    "code": ["code", "visual studio", "pycharm", "intellij", "vim", "neovim", "cursor"],
    "writing": ["word", "docs", "notion", "obsidian", "typora"],
    "terminal": ["terminal", "powershell", "cmd", "windowsterminal", "git bash"],
    "browser_productive": [],  # Will check URLs separately

    # Distracting
    "social": ["twitter", "facebook", "instagram", "tiktok", "reddit"],
    "entertainment": ["youtube", "netflix", "spotify", "vlc", "media player"],
    "messaging": ["whatsapp", "telegram", "discord", "slack", "teams"],
    "games": ["steam", "epic", "game"],
}

# Track app focus time
class ActivityTracker:
    def __init__(self):
        self.current_window = None
        self.current_start = None
        self.sessions = defaultdict(float)  # app -> seconds
        self.today_file = None
        self.running = False
        self._lock = threading.Lock()

    def get_active_window(self) -> Optional[dict]:
        """Get currently active window info."""
        if win32gui is None:
            return None

        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            process = psutil.Process(pid)
            window_title = win32gui.GetWindowText(hwnd)

            return {
                "title": window_title,
                "process": process.name(),
                "pid": pid
            }
        except Exception:
            return None

    def categorize_app(self, process_name: str, title: str) -> str:
        """Categorize an application."""
        combined = (process_name + " " + title).lower()

        for category, keywords in APP_CATEGORIES.items():
            for keyword in keywords:
                if keyword in combined:
                    return category

        # Default categorization by process
        if "chrome" in combined or "firefox" in combined or "edge" in combined:
            # Check title for clues
            for keyword in ["github", "stackoverflow", "docs", "api", "documentation"]:
                if keyword in combined:
                    return "browser_productive"
            for keyword in ["youtube", "reddit", "twitter", "facebook"]:
                if keyword in combined:
                    return "entertainment" if "youtube" in keyword else "social"
            return "browser"

        return "other"

    def record_switch(self, new_window: dict):
        """Record when window focus changes."""
        now = datetime.now()

        with self._lock:
            # Record time spent on previous window
            if self.current_window and self.current_start:
                duration = (now - self.current_start).total_seconds()
                key = self.current_window.get("process", "unknown")
                self.sessions[key] += duration

            # Start tracking new window
            self.current_window = new_window
            self.current_start = now

    def get_today_summary(self) -> dict:
        """Get summary of today's activity."""
        with self._lock:
            # Include current session
            sessions = dict(self.sessions)
            if self.current_window and self.current_start:
                duration = (datetime.now() - self.current_start).total_seconds()
                key = self.current_window.get("process", "unknown")
                sessions[key] = sessions.get(key, 0) + duration

        # Categorize
        by_category = defaultdict(float)
        for app, seconds in sessions.items():
            category = self.categorize_app(app, "")
            by_category[category] += seconds

        # Calculate productivity score
        productive_time = sum(by_category.get(c, 0) for c in ["code", "writing", "terminal", "browser_productive"])
        distracted_time = sum(by_category.get(c, 0) for c in ["social", "entertainment"])
        total_time = sum(sessions.values())

        if total_time > 0:
            productivity_score = int((productive_time / total_time) * 100)
        else:
            productivity_score = 0

        return {
            "total_minutes": int(total_time / 60),
            "productive_minutes": int(productive_time / 60),
            "distracted_minutes": int(distracted_time / 60),
            "productivity_score": productivity_score,
            "top_apps": sorted(sessions.items(), key=lambda x: x[1], reverse=True)[:5],
            "by_category": dict(by_category)
        }

    def save_daily_log(self):
        """Save today's activity to file."""
        today = datetime.now().strftime("%Y-%m-%d")
        filepath = ACTIVITY_DIR / f"{today}.json"

        summary = self.get_today_summary()
        summary["date"] = today
        summary["saved_at"] = datetime.now().isoformat()

        filepath.write_text(json.dumps(summary, indent=2, default=str))
        return filepath

    def get_summary_text(self) -> str:
        """Get human-readable summary."""
        s = self.get_today_summary()

        lines = [
            f"Activity: {s['total_minutes']} min tracked",
            f"Productive: {s['productive_minutes']} min ({s['productivity_score']}%)",
            f"Distracted: {s['distracted_minutes']} min",
            "Top apps:"
        ]

        for app, seconds in s["top_apps"]:
            minutes = int(seconds / 60)
            if minutes > 0:
                lines.append(f"  - {app}: {minutes} min")

        return "\n".join(lines)

    def monitor_loop(self, interval: int = 5):
        """Main monitoring loop."""
        self.running = True
        last_save = datetime.now()

        while self.running:
            window = self.get_active_window()

            if window:
                # Check if window changed
                if (not self.current_window or
                    window.get("pid") != self.current_window.get("pid") or
                    window.get("title") != self.current_window.get("title")):
                    self.record_switch(window)

            # Save every 5 minutes
            if (datetime.now() - last_save).total_seconds() > 300:
                self.save_daily_log()
                last_save = datetime.now()

            time.sleep(interval)

    def start(self):
        """Start monitoring in background thread."""
        thread = threading.Thread(target=self.monitor_loop, daemon=True)
        thread.start()
        return thread

    def stop(self):
        """Stop monitoring."""
        self.running = False
        self.save_daily_log()


# Global tracker instance
_tracker = None

def get_tracker() -> ActivityTracker:
    """Get or create the global tracker."""
    global _tracker
    if _tracker is None:
        _tracker = ActivityTracker()
    return _tracker


def get_activity_context(tracker: Optional[ActivityTracker] = None) -> str:
    """Get activity summary for CEO brief."""
    if tracker is None:
        # Try to load from today's file
        today = datetime.now().strftime("%Y-%m-%d")
        filepath = ACTIVITY_DIR / f"{today}.json"

        if filepath.exists():
            data = json.loads(filepath.read_text())
            lines = [
                f"ACTIVITY TODAY:",
                f"  Total: {data.get('total_minutes', 0)} min",
                f"  Productive: {data.get('productive_minutes', 0)} min",
                f"  Productivity score: {data.get('productivity_score', 0)}%"
            ]
            return "\n".join(lines)
        return ""

    return f"ACTIVITY TODAY:\n{tracker.get_summary_text()}"


if __name__ == "__main__":
    # Test
    tracker = ActivityTracker()
    print("Monitoring for 10 seconds...")
    tracker.start()
    time.sleep(10)
    tracker.stop()
    print(tracker.get_summary_text())
