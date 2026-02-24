"""
Voice Chat for CEO Brief Agent.

Two-way voice conversation with AI assistant.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from voice import Voice, Listener, Conversation
from activity_monitor import get_activity_context, ActivityTracker

try:
    from groq import Groq
except ImportError:
    Groq = None


SYSTEM_PROMPT = """You are a CEO assistant with a female voice named Ada. You help the user stay focused, productive, and accountable.

Your personality:
- Professional but warm
- Direct and concise - keep responses under 3 sentences when possible
- Focused on action and outcomes
- Encouraging but honest - don't sugarcoat

You have access to:
- The user's productivity data (if provided)
- Their recent activity patterns
- Their goals and priorities

When responding:
- Be conversational, not robotic
- Give actionable advice
- Ask follow-up questions when needed
- Remember context from the conversation

Current date/time: {datetime}
"""


class VoiceChat:
    """Voice-based chat with AI assistant."""

    def __init__(self):
        self.voice = Voice()
        self.listener = Listener()
        self.client = Groq() if Groq and os.environ.get("GROQ_API_KEY") else None
        self.conversation_history = []
        self.tracker = None

    def get_system_prompt(self) -> str:
        """Build system prompt with current context."""
        prompt = SYSTEM_PROMPT.format(datetime=datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Add activity context if available
        activity = get_activity_context(self.tracker)
        if activity:
            prompt += f"\n\nUser's activity today:\n{activity}"

        return prompt

    def chat(self, user_input: str) -> str:
        """Send message to AI and get response."""
        if not self.client:
            return "I'm sorry, I can't connect to my brain right now. Please check the API key."

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Keep last 10 exchanges for context
        messages = self.conversation_history[-20:]

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=300,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    *messages
                ]
            )

            assistant_message = response.choices[0].message.content

            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            return f"I encountered an error: {str(e)}"

    def voice_chat_loop(self):
        """Main voice conversation loop."""
        print("\n" + "=" * 50)
        print("  CEO ASSISTANT - VOICE CHAT")
        print("  Say 'goodbye' or 'exit' to end")
        print("=" * 50 + "\n")

        # Greeting
        self.voice.greeting()
        self.voice.speak("How can I help you today?")

        while True:
            # Listen for user input
            user_input = self.listener.listen()

            if not user_input:
                self.voice.speak("I didn't catch that. Could you repeat?")
                continue

            # Check for exit commands
            exit_phrases = ["goodbye", "exit", "quit", "stop", "bye", "end chat"]
            if any(phrase in user_input.lower() for phrase in exit_phrases):
                self.voice.speak("Goodbye. Stay focused and productive!")
                break

            # Get AI response
            print(f"\nYou: {user_input}")
            response = self.chat(user_input)
            print(f"Ada: {response}\n")

            # Speak response
            self.voice.speak(response)

    def quick_question(self, question: str) -> str:
        """Ask a single question via voice and get response."""
        self.voice.speak(question)
        user_input = self.listener.listen()

        if user_input:
            response = self.chat(user_input)
            self.voice.speak(response)
            return response
        return ""

    def daily_checkin(self):
        """Voice-based daily check-in."""
        self.voice.speak("Time for your daily check-in. Let's go through three quick questions.")

        # Question 1: Progress
        self.voice.speak("First, what did you accomplish today?")
        progress = self.listener.listen()
        if not progress:
            progress = "No response"

        # Question 2: Challenges
        self.voice.speak("What felt difficult or what did you avoid?")
        resistance = self.listener.listen()
        if not resistance:
            resistance = "No response"

        # Question 3: Tomorrow
        self.voice.speak("What's your single most important task for tomorrow?")
        tomorrow = self.listener.listen()
        if not tomorrow:
            tomorrow = "No response"

        # Generate brief based on responses
        self.conversation_history.append({
            "role": "user",
            "content": f"Daily check-in:\n- Progress: {progress}\n- Challenges: {resistance}\n- Tomorrow's priority: {tomorrow}\n\nGive me a brief assessment and one piece of advice."
        })

        response = self.chat(
            f"Based on my check-in (progress: {progress}, challenges: {resistance}, tomorrow: {tomorrow}), give me a brief assessment."
        )

        self.voice.speak(response)

        return {
            "progress": progress,
            "resistance": resistance,
            "tomorrow": tomorrow,
            "response": response
        }


def main():
    """Main entry point."""
    if not os.environ.get("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not set")
        print("Set it with: export GROQ_API_KEY=your-key")
        return

    chat = VoiceChat()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "checkin":
            chat.daily_checkin()

        elif cmd == "ask":
            question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "What should I focus on?"
            chat.quick_question(question)

        elif cmd == "text":
            # Text-based chat (no voice)
            print("Text chat mode. Type 'exit' to quit.\n")
            while True:
                user_input = input("You: ").strip()
                if user_input.lower() in ["exit", "quit", "bye"]:
                    break
                response = chat.chat(user_input)
                print(f"Ada: {response}\n")

        else:
            print(f"Unknown command: {cmd}")
            print("Commands: checkin, ask <question>, text")

    else:
        # Default: voice chat
        chat.voice_chat_loop()


if __name__ == "__main__":
    main()
