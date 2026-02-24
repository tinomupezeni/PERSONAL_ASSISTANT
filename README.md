# Ada - Executive AI Operating System

An AI agent inspired by JARVIS that manages your professional life with executive precision. It tracks commitments, compares them against observed behavior, and issues directives.

**Personality:** Calm, factual, decisive. No praise. No encouragement. Just data and directives.

## What We Built

### Core Components

| File | Purpose |
|------|---------|
| `terminal_chat.py` | Main chat interface - Ada speaks, you type |
| `commitments.py` | Commitment tracking and gap analysis |
| `brief.py` | CEO Brief generator - daily accountability reports |
| `memory.py` | Learning system - Ada remembers you |
| `research.py` | Deep web research with synthesis |
| `daemon.py` | Background service that runs scheduled tasks |
| `voice.py` | Text-to-speech (Zira - female voice) |
| `activity_monitor.py` | Tracks active windows and app usage |
| `github_activity.py` | Pulls your GitHub commits |
| `local_docs.py` | Scans local Word documents |
| `google_docs.py` | Google Docs integration (needs setup) |
| `setup_startup.py` | Adds agent to Windows startup |
| `config.json` | Configuration for directories and settings |

### Features Working

- [x] **Ada Voice** - Female voice (Microsoft Zira), JARVIS-style tone
- [x] **Terminal Chat** - Conversational interface with executive AI
- [x] **Commitment Engine** - Track daily commitments with /commit command
- [x] **Gap Analysis** - Compares commitments against observed behavior
- [x] **CEO Directives** - Every brief ends with ONE specific action
- [x] **CEO Brief Generation** - Daily accountability reports via Groq LLM
- [x] **GitHub Integration** - Tracks commits and compares to stated progress
- [x] **Local Document Scanning** - Finds recent Word docs on your PC
- [x] **Pattern Detection** - Notices recurring avoidance across days
- [x] **Brief History** - Saves daily briefs as JSON for pattern analysis
- [x] **Activity Monitoring** - Tracks which apps you use (productivity scoring)
- [x] **Deep Research** - Web search + content extraction + LLM synthesis
- [x] **Memory System** - Ada learns and remembers your goals, projects, patterns
- [x] **Learning Sessions** - Interactive sessions to teach Ada about you

---

## Commitment Engine

The core accountability system. One commitment per day. No excuses.

### How It Works

1. **Evening:** Use `/commit` to set tomorrow's commitment
2. **Next Day:** Work on your commitment
3. **Evening:** Run `brief.py` to generate accountability report
4. **Ada compares** your commitment against observed GitHub/document activity
5. **Issues a CEO Directive** for the next day

### /commit Flow

```
Ada: What is tomorrow's single highest-leverage action?
You: Complete the user registration API

Ada: How will we know it is complete?
You: Endpoint returns 200 with valid JWT

Ada: What will likely distract you?
You: Getting pulled into UI polish work

Ada: Commitment registered.
```

### Storage

```
data/intents/
├── 2026-02-24.json   # Tomorrow's commitment
├── 2026-02-23.json   # Yesterday's (reviewed in today's brief)
└── ...
```

### Brief Output Format

```
COMMITMENT REVIEW:
Yesterday's commitment "Complete API endpoint" was not fulfilled.
No commits related to registration were detected.

MOMENTUM:
Built CEO Brief agent with commitment tracking.

RISK:
Dissertation work avoided for 3rd consecutive day.

PATTERN:
Recurring avoidance: dissertation-related tasks.

CEO DIRECTIVE:
Write 500 words of dissertation Chapter 2 before any coding.
```

---

## Research System

Ada can research any topic by searching the web, fetching content from multiple sources, and synthesizing an executive briefing.

### Commands

```
/research <topic>   Deep research with synthesis (5 sources)
/search <query>     Quick search results only
```

### How It Works

1. **Search** - DuckDuckGo search for relevant sources
2. **Fetch** - Extracts text content from top results
3. **Synthesize** - LLM generates executive summary with citations

### Example

```
You: /research microservices architecture

(Researching: microservices architecture...)

==================================================
  RESEARCH: MICROSERVICES ARCHITECTURE
==================================================

Microservices architecture is a design approach where applications
are built as a collection of small, independent services...

Key Insights:
- Each service runs its own process [1]
- Services communicate via APIs [2]
- Enables independent deployment [3]

Sources:
  [1] Martin Fowler - Microservices
      https://martinfowler.com/...
```

---

## Memory & Learning

Ada learns about you over time. She remembers your goals, projects, patterns, and facts.

### Commands

```
/learn              Interactive learning session
/learn <fact>       Teach Ada a specific fact
/goal <goal>        Add a goal
/project <name>     Add a project
/memory             Show what Ada knows about you
/status             Full status report with memory
```

### What Ada Remembers

| Category | Examples |
|----------|----------|
| **Profile** | Name, role, working hours |
| **Goals** | Your primary objectives |
| **Projects** | Active work |
| **Facts** | "I work best in the morning" |
| **Patterns** | Avoidance triggers, distractions |
| **Insights** | Inferred from behavior |

### Learning Session

```
You: /learn

==================================================
  LEARNING SESSION
==================================================

What should I call you?
> Marcus

What is your primary role?
> Software Engineer

What are your primary goals? (empty line to finish)
> Ship the MVP by March
> Finish dissertation
>

What projects are you working on?
> Ada AI Agent
> E-commerce platform
>

Any important facts?
> I work best before noon
> I get distracted by YouTube
>

==================================================
  Learning complete. I now know:
==================================================

USER MEMORY:
Name: Marcus
Role: Software Engineer
Goals: Ship the MVP by March, Finish dissertation
Projects: Ada AI Agent, E-commerce platform

Known Facts:
  - I work best before noon
  - I get distracted by YouTube
```

### How Memory Works

- Stored in `data/memory/` as JSON files
- Loaded into every LLM prompt automatically
- Ada references your goals/projects by name
- Patterns learned from brief responses

---

## Design Philosophy (JARVIS-Inspired)

Based on Tony Stark's AI assistant from Iron Man:

| Principle | Implementation |
|-----------|----------------|
| **Calm, measured** | No exclamation marks, no enthusiasm |
| **Factual** | "No commits detected" not "You didn't code today" |
| **Decisive** | "CEO DIRECTIVE: [action]" not "You might consider..." |
| **No praise** | Never says "Great job!" or "Well done!" |
| **No motivation** | Never says "You can do it!" or "Keep going!" |
| **Dry wit** | Occasional understated observations |

### What Ada Says vs Doesn't Say

| Instead of... | Ada says... |
|---------------|-------------|
| "Great progress today!" | *(nothing, or states the fact)* |
| "You should consider..." | "Directive: [action]" |
| "I believe in you!" | "The data indicates [X]" |
| "Don't worry about it" | "Gap detected. Proceeding." |
| "You're doing amazing!" | *(never)* |

---

## Quick Start

### 1. Set Environment Variables (Required)

```powershell
# PowerShell - set permanently
[System.Environment]::SetEnvironmentVariable('GROQ_API_KEY', 'YOUR_GROQ_API_KEY_HERE', 'User')
[System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'YOUR_GITHUB_TOKEN_HERE', 'User')
```

Or for current session only:
```cmd
set GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
set GITHUB_TOKEN=YOUR_GITHUB_TOKEN_HERE
```

### 2. Install Dependencies

```bash
cd C:\Users\Dell\Documents\projects\Agent
pip install -r requirements.txt
```

### 3. Run

```bash
# Chat with Ada
python terminal_chat.py

# Generate a CEO Brief
python brief.py

# Run the daemon (scheduled tasks)
python daemon.py
```

---

## Usage

### Terminal Chat with Ada

```bash
python terminal_chat.py
```

Commands:
- Type anything to chat
- `scan` - Show raw PC data (documents, GitHub, activity)
- `mute` - Silence Ada's voice
- `unmute` - Enable voice
- `exit` - Quit

### CEO Brief (Manual)

```bash
# Interactive mode - answer 3 questions
python brief.py

# CLI mode - pass answers directly
python brief.py "What I did today" "What was hard" "Tomorrow's priority"
```

### Daemon Commands

```bash
python daemon.py          # Run background service
python daemon.py chat     # Start terminal chat
python daemon.py brief    # Generate and speak brief
python daemon.py test     # Test voice
python daemon.py status   # Show activity stats
```

### Windows Startup

```bash
python setup_startup.py add      # Add to startup
python setup_startup.py remove   # Remove from startup
python setup_startup.py check    # Check if in startup
```

---

## Configuration

Edit `config.json`:

```json
{
  "document_directories": [
    "C:/Users/Dell/Documents",
    "C:/Users/Dell/Desktop",
    "C:/Users/Dell/Downloads"
  ],
  "scan_days": 14,
  "track_repos": []
}
```

---

## Architecture

```
User Input (typing)
       │
       ▼
┌─────────────────┐
│  terminal_chat  │ ◄── You type here
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│   Groq LLM      │ ◄───│  PC Context      │
│ (llama-3.3-70b) │     │  - Documents     │
└────────┬────────┘     │  - GitHub        │
         │              │  - Activity      │
         ▼              └──────────────────┘
┌─────────────────┐
│   Ada Voice     │ ──► Speaker (Zira)
│   (pyttsx3)     │
└─────────────────┘
```

---

## Data Storage

```
Agent/
├── data/
│   ├── briefs/           # Daily CEO briefs (JSON)
│   │   └── 2026-02-24.json
│   ├── intents/          # Daily commitments (JSON)
│   │   └── 2026-02-25.json
│   ├── activity/         # Daily activity logs (JSON)
│   │   └── 2026-02-24.json
│   ├── memory/           # User profile and patterns
│   │   ├── profile.json
│   │   ├── facts.json
│   │   ├── patterns.json
│   │   └── insights.json
│   └── research/         # Research history (JSON)
│       └── 20260225_1430_topic.json
└── prompts/
    └── ceo_brief.txt     # Customizable prompt rules
```

---

## What's Missing / TODO

### High Priority

- [ ] **Voice Input Not Working** - Speech recognition via Google/Whisper is unreliable. Currently using typed input as workaround.

- [ ] **Daemon Not Persistent** - The daemon stops when terminal closes. Needs proper Windows service or Task Scheduler setup.

- [ ] **Google Docs Integration** - Code exists but requires OAuth setup:
  1. Create Google Cloud project
  2. Enable Drive + Docs APIs
  3. Download `credentials.json` to Agent folder
  4. Run once to authenticate

- [ ] **Environment Variables** - Must be set manually each session unless added permanently to Windows.

### Medium Priority

- [ ] **GUI Interface** - Currently terminal-only. Could add system tray icon or desktop widget.

- [ ] **Notification System** - No push notifications. Agent only speaks when you're in chat.

- [ ] **Calendar Integration** - Could connect to Google Calendar or Outlook for scheduled tasks.

- [ ] **Email Scanning** - Could check for important emails and summarize.

- [ ] **Browser History** - Could analyze browsing patterns for productivity insights.

### Low Priority

- [ ] **Mobile App** - WhatsApp/Telegram bot for remote briefings.

- [ ] **Multiple Voices** - Option to choose different voice/personality.

- [ ] **Offline Mode** - Use local LLM (Ollama) when internet unavailable.

- [ ] **Dashboard** - Web-based dashboard showing productivity trends.

---

## Known Issues

1. **Voice Only Speaks Once** - Fixed by reinitializing pyttsx3 engine for each speak() call.

2. **Document Scan Slow** - Limited to 50 files max and specific directories to prevent hanging.

3. **Speech Recognition Fails** - Google Speech API doesn't recognize audio well. Groq Whisper works better but still unreliable.

---

## The Vision

This agent is meant to evolve through versions:

| Version | Role | Capability |
|---------|------|------------|
| V1 | Reporter | Tells what happened |
| V2 | Analyst | Explains why |
| V3 | Coach | Recommends actions |
| V4 | Operator | Schedules tasks automatically |
| V5 | Chief of Staff | Manages projects proactively |

**Current State: V1-V2** (Reporter + Basic Analysis)

---

## Files Reference

| File | Lines | Description |
|------|-------|-------------|
| `terminal_chat.py` | ~470 | Main chat interface with all commands |
| `brief.py` | ~200 | CEO brief generator |
| `memory.py` | ~410 | Learning and memory system |
| `research.py` | ~265 | Deep web research |
| `commitments.py` | ~150 | Commitment tracking |
| `daemon.py` | ~230 | Background service |
| `voice.py` | ~320 | Voice output |
| `activity_monitor.py` | ~200 | Window tracking |
| `github_activity.py` | ~120 | GitHub API |
| `local_docs.py` | ~150 | Document scanner |
| `google_docs.py` | ~180 | Google Docs API |
| `setup_startup.py` | ~100 | Windows startup |
| `config.json` | 9 | Configuration |
| `requirements.txt` | 14 | Dependencies |

---

## Requirements

```
groq>=0.4.0
requests>=2.28.0
python-docx>=0.8.11
ddgs>=6.0.0
beautifulsoup4>=4.12.0
google-auth>=2.0.0
google-auth-oauthlib>=1.0.0
google-api-python-client>=2.0.0
pyttsx3>=2.90
pywin32>=306
psutil>=5.9.0
schedule>=1.2.0
```

---

## Next Steps

1. **Make Daemon Persistent** - Set up as Windows Service or Task Scheduler job
2. **Fix Voice Input** - Either improve Whisper integration or accept typed input
3. **Add System Tray** - Minimal GUI for quick access
4. **Connect Google Docs** - Complete OAuth flow
5. **Daily Habit** - Actually use it every day for 2 weeks to test

---

*Built with Claude Code + Groq + Python*
