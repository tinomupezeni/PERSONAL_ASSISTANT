"""
CEO Brief Agent Daemon.

Runs continuously, monitoring activity and delivering briefings.
"""

import os
import sys
import json
import time
import threading
import schedule
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from activity_monitor import ActivityTracker, get_activity_context
from voice import Voice, speak, speak_brief
from brief import generate_brief, get_recent_briefs, save_brief, load_config
from sync import sync_to_github, get_sync_status
from self_analysis import run_full_analysis, get_open_gaps

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
LOG_FILE = BASE_DIR / "data" / "daemon.log"


def log(message: str):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


class CEOAgent:
    def __init__(self):
        self.tracker = ActivityTracker()
        self.voice = Voice()
        self.running = False
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load daemon configuration."""
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
        return {}

    def startup_greeting(self):
        """Greet user on startup."""
        log("Agent starting up...")
        self.voice.greeting()

    def morning_brief(self):
        """Deliver morning CEO brief."""
        log("Generating morning brief...")

        try:
            # Get activity from yesterday if available
            activity = get_activity_context()

            # Create a brief using recent history
            recent = get_recent_briefs(7)

            # Use last answers as base, or defaults
            if recent:
                last = recent[0]
                answers = last.get("answers", {})
                # Modify for morning context
                answers["progress"] = f"Yesterday: {answers.get('progress', 'No data')}"
            else:
                answers = {
                    "progress": "Starting fresh day",
                    "resistance": "Unknown",
                    "tomorrow": "Set priorities"
                }

            brief = generate_brief(answers, recent)

            # Speak the brief
            log("Speaking morning brief...")
            self.voice.speak("Good morning. Here is your CEO brief.")
            self.voice.speak_brief(brief)

            # Save
            save_brief(answers, brief)
            log("Morning brief complete.")

        except Exception as e:
            log(f"Error generating brief: {e}")

    def focus_check(self):
        """Periodic focus check - alert if too much distraction."""
        summary = self.tracker.get_today_summary()

        productivity = summary.get("productivity_score", 100)
        distracted_mins = summary.get("distracted_minutes", 0)

        # Alert if productivity drops below 40% after significant time
        if summary.get("total_minutes", 0) > 30:
            if productivity < 40:
                self.voice.alert(
                    f"Focus check. Productivity at {productivity}%. "
                    f"{distracted_mins} minutes on distractions."
                )
                log(f"Focus alert: {productivity}% productivity")

    def evening_review(self):
        """Evening review and reflection prompt."""
        log("Evening review...")

        summary = self.tracker.get_today_summary()
        self.tracker.save_daily_log()

        productivity = summary.get("productivity_score", 0)
        total = summary.get("total_minutes", 0)

        message = (
            f"End of day review. "
            f"You tracked {total} minutes today. "
            f"Productivity score: {productivity}%. "
            f"Time to reflect on tomorrow's priorities."
        )

        self.voice.speak(message)
        log("Evening review complete.")

    def auto_sync(self):
        """Automatically sync to GitHub."""
        log("Auto-syncing to GitHub...")

        try:
            result = sync_to_github()

            if result["success"]:
                log(f"Sync complete: {result.get('message', 'Done')}")
            else:
                log(f"Sync failed: {result.get('error', 'Unknown')}")

        except Exception as e:
            log(f"Sync error: {e}")

    def weekly_analysis(self):
        """Weekly self-analysis."""
        log("Running weekly self-analysis...")

        try:
            results = run_full_analysis()
            new_gaps = len(results.get("new_gaps", []))
            total_gaps = len(get_open_gaps())

            log(f"Analysis complete: {new_gaps} new gaps, {total_gaps} total open")

            # Notify user if critical gaps found
            critical = [g for g in get_open_gaps() if g.get("severity") == "critical"]
            if critical:
                self.voice.alert(
                    f"Weekly analysis complete. {len(critical)} critical gaps identified. "
                    f"Use /improve for details."
                )

        except Exception as e:
            log(f"Analysis error: {e}")

    def run_schedule(self):
        """Run scheduled tasks."""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def start(self):
        """Start the CEO Agent daemon."""
        self.running = True

        # Startup
        self.startup_greeting()

        # Start activity monitoring
        log("Starting activity monitor...")
        self.tracker.start()

        # Schedule tasks
        schedule.every().day.at("08:00").do(self.morning_brief)
        schedule.every().day.at("12:00").do(self.focus_check)
        schedule.every().day.at("15:00").do(self.focus_check)
        schedule.every().day.at("18:00").do(self.evening_review)

        # Also run focus check every 2 hours during work hours
        schedule.every(2).hours.do(self.focus_check)

        # Auto-sync to GitHub every 6 hours
        schedule.every(6).hours.do(self.auto_sync)

        # Weekly self-analysis on Sundays at 20:00
        schedule.every().sunday.at("20:00").do(self.weekly_analysis)

        log("Daemon running. Scheduled tasks:")
        log("  - 08:00: Morning brief")
        log("  - 12:00, 15:00: Focus checks")
        log("  - 18:00: Evening review")
        log("  - Every 2h: Focus check")
        log("  - Every 6h: GitHub sync")
        log("  - Sunday 20:00: Self-analysis")

        # Run scheduler in main thread
        try:
            self.run_schedule()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the daemon."""
        log("Stopping daemon...")
        self.running = False
        self.tracker.stop()
        log("Daemon stopped.")


def main():
    """Main entry point."""
    # Check for required env vars
    if not os.environ.get("GROQ_API_KEY"):
        print("Warning: GROQ_API_KEY not set. Briefs will fail.")

    agent = CEOAgent()

    # Handle command line args
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "brief":
            # Generate and speak a brief now
            agent.morning_brief()

        elif cmd == "status":
            # Show current status
            summary = agent.tracker.get_today_summary()
            print(agent.tracker.get_summary_text())

        elif cmd == "speak":
            # Speak remaining args
            text = " ".join(sys.argv[2:])
            speak(text)

        elif cmd == "test":
            # Test voice
            agent.voice.speak("CEO Agent voice test successful.")

        elif cmd == "chat":
            # Start terminal chat (Ada speaks, you type)
            from terminal_chat import TerminalChat
            chat = TerminalChat()
            chat.run()

        elif cmd == "checkin":
            # Voice-based daily check-in
            from chat import VoiceChat
            chat = VoiceChat()
            chat.daily_checkin()

        elif cmd == "listen":
            # Just listen for one command
            from voice import Listener
            listener = Listener()
            text = listener.listen("I'm listening.")
            if text:
                print(f"You said: {text}")
                agent.voice.speak(f"You said: {text}")

        elif cmd == "sync":
            # Sync to GitHub now
            from sync import sync_to_github, get_sync_status
            print(get_sync_status())
            print("\nSyncing...")
            result = sync_to_github()
            if result["success"]:
                print(f"Success: {result.get('message', 'Done')}")
            else:
                print(f"Error: {result.get('error', 'Unknown')}")

        elif cmd == "analyze":
            # Run self-analysis
            from self_analysis import run_full_analysis, get_gaps_summary
            results = run_full_analysis()
            print(get_gaps_summary())

        else:
            print(f"Unknown command: {cmd}")
            print("Commands: brief, status, speak <text>, test, chat, checkin, listen, sync, analyze")

    else:
        # Run daemon
        agent.start()


if __name__ == "__main__":
    main()
