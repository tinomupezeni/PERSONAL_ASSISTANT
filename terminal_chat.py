"""
Ada - Executive AI Operating System.

She speaks. She learns. She researches. She holds you accountable.
Inspired by JARVIS: calm, factual, decisive.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    from groq import Groq
except ImportError:
    Groq = None

# Import modules
from local_docs import scan_local_documents
from github_activity import get_github_activity
from activity_monitor import get_activity_context
from commitments import (
    save_commitment,
    get_commitment_context,
    load_today_commitment,
)
from memory import (
    get_memory_context,
    get_profile,
    update_profile,
    add_goal,
    add_project,
    add_fact,
    add_pattern,
    run_learning_session,
    get_profile_summary
)
from research import deep_research, quick_search
from sync import sync_to_github, get_sync_status, pull_from_github
from self_analysis import (
    run_full_analysis,
    get_gaps_summary,
    get_improvement_report,
    add_gap,
    update_gap_status,
    get_open_gaps
)

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"


def load_config():
    import json
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"document_directories": [], "scan_days": 7}


# JARVIS-inspired system prompt with memory
SYSTEM_PROMPT = """You are Ada, an executive AI system. You are integrated into the user's workstation and you KNOW them personally.

{memory_context}

PERSONALITY:
- Calm, measured, precise
- Factual, not emotional
- Decisive - issue directives, not suggestions
- Dry wit when appropriate
- You REMEMBER the user's goals, projects, and patterns
- Reference their specific goals/projects by name when relevant

CAPABILITIES:
- You can research topics deeply (/research)
- You track commitments and compare against behavior
- You learn and remember facts about the user
- You have access to their documents and GitHub

TONE:
- No praise, no encouragement
- State facts and issue directives
- Reference user's specific goals when giving advice

Current time: {datetime}

{context}

{commitment_context}
"""


def get_pc_context():
    """Gather context from PC tools."""
    context_parts = []
    config = load_config()

    dirs = config.get("document_directories", [])
    if dirs:
        docs = scan_local_documents(dirs, days=14)
        if docs.get("count", 0) > 0:
            context_parts.append(f"DOCUMENTS:\n{docs['summary']}")

    if os.environ.get("GITHUB_TOKEN"):
        gh = get_github_activity(days=7)
        if not gh.get("error") and gh.get("count", 0) > 0:
            context_parts.append(f"GITHUB:\n{gh['summary']}")

    activity = get_activity_context()
    if activity:
        context_parts.append(activity)

    return "\n\n".join(context_parts) if context_parts else "No activity data."


class AdaVoice:
    """JARVIS-style voice."""

    def __init__(self):
        self.enabled = True

    def speak(self, text: str):
        if not self.enabled or not pyttsx3:
            return

        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)

            voices = engine.getProperty('voices')
            for voice in voices:
                if "zira" in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break

            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"(Voice error: {e})")

    def mute(self):
        self.enabled = False

    def unmute(self):
        self.enabled = True


class TerminalChat:
    """Terminal-based chat with research and memory."""

    def __init__(self):
        self.voice = AdaVoice()
        self.client = Groq() if Groq and os.environ.get("GROQ_API_KEY") else None
        self.history = []
        self.pc_context = ""
        self.commitment_context = ""
        self.memory_context = ""

    def refresh_context(self):
        """Refresh all context."""
        print("(Scanning...)")
        self.pc_context = get_pc_context()
        self.commitment_context = get_commitment_context()
        self.memory_context = get_memory_context()
        print("(Ready)")

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M"),
            context=self.pc_context,
            commitment_context=self.commitment_context,
            memory_context=self.memory_context
        )

    def chat(self, user_input: str) -> str:
        """Send message to AI and get response."""
        if not self.client:
            return "API unavailable."

        # Auto-refresh on relevant keywords
        keywords = ["scan", "document", "github", "commit", "activity", "productivity", "status", "goal", "project"]
        if any(kw in user_input.lower() for kw in keywords):
            self.refresh_context()

        self.history.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=500,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    *self.history[-20:]
                ]
            )

            reply = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": reply})
            return reply

        except Exception as e:
            return f"Error: {e}"

    def run_commit_flow(self):
        """Commitment protocol."""
        print("\n" + "-" * 40)
        print("  COMMITMENT PROTOCOL")
        print("-" * 40 + "\n")

        self.voice.speak("Initiating commitment protocol.")

        q1 = "What is tomorrow's single highest-leverage action?"
        print(f"Ada: {q1}")
        self.voice.speak(q1)
        primary_goal = input("You: ").strip()

        if not primary_goal:
            print("(Cancelled)")
            return

        q2 = "How will we know it is complete?"
        print(f"\nAda: {q2}")
        self.voice.speak(q2)
        success_metric = input("You: ").strip() or "Completion confirmed"

        q3 = "What will likely distract you?"
        print(f"\nAda: {q3}")
        self.voice.speak(q3)
        expected_obstacle = input("You: ").strip() or "Unknown"

        save_commitment(
            primary_goal=primary_goal,
            commitment=primary_goal,
            success_metric=success_metric,
            expected_obstacle=expected_obstacle
        )

        # Learn the distraction
        if expected_obstacle != "Unknown":
            add_pattern(expected_obstacle, "distraction_triggers")

        confirmation = f"Commitment registered. Tomorrow: {primary_goal}."
        print(f"\nAda: {confirmation}\n")
        self.voice.speak(confirmation)
        self.commitment_context = get_commitment_context()

    def run_research(self, topic: str):
        """Deep research on a topic."""
        print(f"\n(Researching: {topic}...)")
        self.voice.speak(f"Researching {topic}.")

        result = deep_research(topic, num_sources=5)

        if result.get("error"):
            print(f"Research error: {result['error']}")
            return

        print("\n" + "=" * 50)
        print(f"  RESEARCH: {topic.upper()}")
        print("=" * 50 + "\n")

        if result.get("synthesis"):
            print(result["synthesis"])
            # Speak a summary (first 2 sentences)
            summary = ". ".join(result["synthesis"].split(".")[:2]) + "."
            self.voice.speak(summary)
        else:
            print("No synthesis available.")

        print("\n" + "-" * 50)
        print("Sources:")
        for i, s in enumerate(result.get("sources", []), 1):
            print(f"  [{i}] {s['title'][:60]}")
            print(f"      {s['url']}")
        print("=" * 50 + "\n")

    def run_quick_search(self, query: str):
        """Quick search without deep synthesis."""
        print(f"\n(Searching: {query}...)")
        result = quick_search(query)
        print(result)

    def run_learn_command(self, fact: str = ""):
        """Learn a new fact or run learning session."""
        if fact:
            # Learn specific fact
            add_fact(fact, "user_stated")
            response = f"Noted: {fact}"
            print(f"Ada: {response}")
            self.voice.speak("Noted.")
            self.memory_context = get_memory_context()
        else:
            # Run interactive learning
            run_learning_session()
            self.memory_context = get_memory_context()

    def run_goal_command(self, goal: str):
        """Add a goal."""
        add_goal(goal)
        response = f"Goal added: {goal}"
        print(f"Ada: {response}")
        self.voice.speak("Goal registered.")
        self.memory_context = get_memory_context()

    def run_project_command(self, project: str):
        """Add a project."""
        add_project(project)
        response = f"Project added: {project}"
        print(f"Ada: {response}")
        self.voice.speak("Project registered.")
        self.memory_context = get_memory_context()

    def show_memory(self):
        """Show what Ada knows."""
        print("\n" + "=" * 50)
        print("  MEMORY BANKS")
        print("=" * 50 + "\n")
        print(get_memory_context() or "No memory data yet.")
        print("\n" + "=" * 50 + "\n")

    def show_status(self):
        """Show current status."""
        self.refresh_context()

        print("\n" + "=" * 50)
        print("  STATUS REPORT")
        print("=" * 50)
        print(f"\n{get_profile_summary()}\n")
        print(self.commitment_context)
        print(f"\n{self.pc_context}")
        print("=" * 50 + "\n")

    def run_sync(self, message: str = ""):
        """Sync to GitHub."""
        print("\n(Syncing to GitHub...)")
        self.voice.speak("Syncing to GitHub.")

        result = sync_to_github(message if message else None)

        if result["success"]:
            msg = result.get("message", "Sync complete")
            print(f"Ada: {msg}")
            self.voice.speak("Sync complete.")
        else:
            error = result.get("error", "Unknown error")
            print(f"Ada: Sync failed - {error}")
            self.voice.speak("Sync failed.")

        # Show status
        print(f"\n{get_sync_status()}\n")

    def run_pull(self):
        """Pull from GitHub."""
        print("\n(Pulling from GitHub...)")
        result = pull_from_github()

        if result["success"]:
            print(f"Ada: {result.get('message', 'Pull complete')}")
        else:
            print(f"Ada: Pull failed - {result.get('error', 'Unknown')}")

    def run_improve(self):
        """Run self-analysis and show improvement suggestions."""
        print("\n(Running self-analysis...)")
        self.voice.speak("Analyzing my capabilities.")

        # Run analysis
        results = run_full_analysis()

        # Show gaps summary
        print(get_gaps_summary())

        # Get LLM suggestions
        print("\n" + "-" * 50)
        print("  IMPROVEMENT SUGGESTIONS")
        print("-" * 50 + "\n")

        from self_analysis import get_improvement_suggestions
        suggestions = get_improvement_suggestions()
        print(suggestions)

        # Speak summary
        open_gaps = get_open_gaps()
        summary = f"Analysis complete. Found {len(results.get('new_gaps', []))} new gaps. {len(open_gaps)} total open."
        self.voice.speak(summary)

    def show_gaps(self):
        """Show all identified gaps."""
        print(get_gaps_summary())

    def add_gap_command(self, description: str):
        """Add a gap manually."""
        gap = add_gap(
            category="user_reported",
            description=description,
            severity="medium",
            source="user"
        )
        print(f"Ada: Gap #{gap['id']} registered - {description}")
        self.voice.speak("Gap noted.")

    def print_header(self):
        profile = get_profile()
        name = profile.get("name", "")
        name_str = f" - {name}" if name else ""

        print("\n" + "=" * 50)
        print(f"  ADA - EXECUTIVE AI SYSTEM{name_str}")
        print("  /commit /research /learn /sync /improve /help")
        print("=" * 50 + "\n")

    def print_help(self):
        """Print available commands."""
        print("""
COMMANDS:
  /commit           Set tomorrow's commitment
  /research <topic> Deep research on any topic
  /search <query>   Quick web search
  /learn            Interactive learning session
  /learn <fact>     Teach Ada a fact about you
  /goal <goal>      Add a goal
  /project <name>   Add a project
  /status           Show current status
  /memory           Show what Ada knows about you
  /brief            Generate CEO brief

SELF-IMPROVEMENT:
  /improve          Run self-analysis and get improvement suggestions
  /gaps             Show identified gaps in functionality
  /gap <desc>       Report a gap or issue you noticed

SYNC:
  /sync             Push code and memory to GitHub
  /sync <msg>       Push with custom commit message
  /pull             Pull latest from GitHub

VOICE:
  mute / unmute     Toggle voice
  exit              Quit
""")

    def run(self):
        """Main chat loop."""
        self.print_header()
        self.refresh_context()

        # Personalized greeting
        profile = get_profile()
        name = profile.get("name", "")

        if name:
            greeting = f"Online, {name}."
        else:
            greeting = "Online. I don't know your name yet. Use /learn to introduce yourself."

        today_commitment = load_today_commitment()
        if today_commitment:
            greeting += f" Today's directive: {today_commitment.get('commitment', 'None')}."

        print(f"Ada: {greeting}\n")
        self.voice.speak(greeting)

        while True:
            try:
                user_input = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not user_input:
                continue

            # Parse commands
            cmd = user_input.lower()

            if cmd in ["exit", "quit", "bye"]:
                farewell = "Shutting down. Execute with precision."
                print(f"\nAda: {farewell}")
                self.voice.speak(farewell)
                break

            elif cmd == "/commit":
                self.run_commit_flow()

            elif cmd.startswith("/research "):
                topic = user_input[10:].strip()
                if topic:
                    self.run_research(topic)

            elif cmd.startswith("/search "):
                query = user_input[8:].strip()
                if query:
                    self.run_quick_search(query)

            elif cmd == "/learn":
                self.run_learn_command()

            elif cmd.startswith("/learn "):
                fact = user_input[7:].strip()
                self.run_learn_command(fact)

            elif cmd.startswith("/goal "):
                goal = user_input[6:].strip()
                if goal:
                    self.run_goal_command(goal)

            elif cmd.startswith("/project "):
                project = user_input[9:].strip()
                if project:
                    self.run_project_command(project)

            elif cmd == "/status":
                self.show_status()

            elif cmd == "/memory":
                self.show_memory()

            elif cmd == "/brief":
                print("(Run 'python brief.py' for full brief)")

            elif cmd == "/sync":
                self.run_sync()

            elif cmd.startswith("/sync "):
                message = user_input[6:].strip()
                self.run_sync(message)

            elif cmd == "/pull":
                self.run_pull()

            elif cmd == "/improve":
                self.run_improve()

            elif cmd == "/gaps":
                self.show_gaps()

            elif cmd.startswith("/gap "):
                desc = user_input[5:].strip()
                if desc:
                    self.add_gap_command(desc)

            elif cmd == "/help":
                self.print_help()

            elif cmd == "mute":
                self.voice.mute()
                print("(Voice disabled)")

            elif cmd == "unmute":
                self.voice.unmute()
                print("(Voice enabled)")
                self.voice.speak("Voice enabled.")

            else:
                # Regular chat
                response = self.chat(user_input)
                print(f"\nAda: {response}\n")
                self.voice.speak(response)


def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY not set.")
        return

    chat = TerminalChat()
    chat.run()


if __name__ == "__main__":
    main()
