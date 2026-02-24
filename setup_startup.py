"""
Windows Startup Setup for CEO Agent.

Adds or removes the agent from Windows startup.
"""

import os
import sys
import winreg
from pathlib import Path


AGENT_DIR = Path(__file__).parent
DAEMON_SCRIPT = AGENT_DIR / "daemon.py"
STARTUP_NAME = "CEOAgent"


def get_python_path() -> str:
    """Get the path to Python executable."""
    return sys.executable


def create_startup_command() -> str:
    """Create the command to run the daemon."""
    python = get_python_path()
    script = str(DAEMON_SCRIPT)

    # Use pythonw for no console window, or python for visible console
    pythonw = python.replace("python.exe", "pythonw.exe")
    if os.path.exists(pythonw):
        python = pythonw

    return f'"{python}" "{script}"'


def add_to_startup():
    """Add CEO Agent to Windows startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        command = create_startup_command()
        winreg.SetValueEx(key, STARTUP_NAME, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)

        print(f"Added to startup: {STARTUP_NAME}")
        print(f"Command: {command}")
        return True

    except Exception as e:
        print(f"Failed to add to startup: {e}")
        return False


def remove_from_startup():
    """Remove CEO Agent from Windows startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        winreg.DeleteValue(key, STARTUP_NAME)
        winreg.CloseKey(key)

        print(f"Removed from startup: {STARTUP_NAME}")
        return True

    except FileNotFoundError:
        print("Not in startup.")
        return True

    except Exception as e:
        print(f"Failed to remove from startup: {e}")
        return False


def check_startup() -> bool:
    """Check if CEO Agent is in startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )

        try:
            value, _ = winreg.QueryValueEx(key, STARTUP_NAME)
            print(f"In startup: {value}")
            return True
        except FileNotFoundError:
            print("Not in startup.")
            return False
        finally:
            winreg.CloseKey(key)

    except Exception as e:
        print(f"Error checking startup: {e}")
        return False


def create_env_script():
    """Create a batch script that sets environment variables and runs daemon."""
    env_script = AGENT_DIR / "run_agent.bat"

    # Read current env vars or use placeholders
    groq_key = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN")

    content = f'''@echo off
set GROQ_API_KEY={groq_key}
set GITHUB_TOKEN={github_token}
cd /d "{AGENT_DIR}"
python daemon.py
'''

    env_script.write_text(content)
    print(f"Created: {env_script}")
    print("Edit this file to set your API keys if needed.")
    return env_script


def setup_task_scheduler():
    """Alternative: Use Task Scheduler for more control."""
    print("""
To use Task Scheduler instead (recommended for reliability):

1. Open Task Scheduler (taskschd.msc)
2. Create Basic Task: "CEO Agent"
3. Trigger: "When I log on"
4. Action: Start a program
   - Program: python
   - Arguments: "C:\\Users\\Dell\\Documents\\projects\\Agent\\daemon.py"
   - Start in: "C:\\Users\\Dell\\Documents\\projects\\Agent"
5. Check "Open Properties dialog" and set:
   - "Run whether user is logged on or not" (optional)
   - Add environment variables in the Settings tab

This gives you more control over the agent lifecycle.
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python setup_startup.py [add|remove|check|script|scheduler]")
        print("")
        print("Commands:")
        print("  add       - Add to Windows startup")
        print("  remove    - Remove from Windows startup")
        print("  check     - Check if in startup")
        print("  script    - Create run_agent.bat with env vars")
        print("  scheduler - Show Task Scheduler instructions")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "add":
        create_env_script()
        add_to_startup()
    elif cmd == "remove":
        remove_from_startup()
    elif cmd == "check":
        check_startup()
    elif cmd == "script":
        create_env_script()
    elif cmd == "scheduler":
        setup_task_scheduler()
    else:
        print(f"Unknown command: {cmd}")
