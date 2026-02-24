"""
Voice I/O for CEO Brief Agent.

Text-to-speech and speech recognition for voice conversations.
"""

import os
import threading
import tempfile
from typing import Optional, Callable

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from groq import Groq
except ImportError:
    Groq = None


class Voice:
    def __init__(
        self,
        rate: int = 165,
        volume: float = 1.0,
        voice_name: str = "zira"  # Use Zira (female) by default
    ):
        """
        Initialize voice engine with female voice.

        Args:
            rate: Speech rate (words per minute). Default 165.
            volume: Volume 0.0 to 1.0. Default 1.0.
            voice_name: Part of voice name to match (case-insensitive).
        """
        if pyttsx3 is None:
            self.engine = None
            return

        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)

        # Find and set the requested voice
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if voice_name.lower() in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break

    def list_voices(self) -> list[dict]:
        """List available voices."""
        if not self.engine:
            return []

        voices = self.engine.getProperty('voices')
        return [
            {"id": i, "name": v.name, "lang": getattr(v, 'languages', [])}
            for i, v in enumerate(voices)
        ]

    def speak(self, text: str, block: bool = True):
        """
        Speak text.

        Args:
            text: Text to speak
            block: If True, wait for speech to complete
        """
        if not self.engine:
            print(f"[Voice disabled] {text}")
            return

        if block:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            thread = threading.Thread(
                target=self._speak_async,
                args=(text,),
                daemon=True
            )
            thread.start()

    def _speak_async(self, text: str):
        """Speak in background thread."""
        engine = pyttsx3.init()
        engine.setProperty('rate', 165)
        # Set female voice
        voices = engine.getProperty('voices')
        for voice in voices:
            if "zira" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        engine.say(text)
        engine.runAndWait()

    def speak_brief(self, brief: str):
        """Speak a CEO brief in a natural way."""
        if not self.engine:
            print(f"[Voice disabled] {brief}")
            return

        # Clean up for speech
        text = brief.replace("MOMENTUM:", "Momentum.")
        text = text.replace("RISK:", "Risk.")
        text = text.replace("PATTERN:", "Pattern.")
        text = text.replace("ACTION:", "Recommended action.")
        text = text.replace("\n", " ")

        intro = "Here is your CEO brief."
        full_text = f"{intro} {text}"

        self.speak(full_text)

    def alert(self, message: str):
        """Speak an alert message."""
        self.speak(f"Attention. {message}")

    def greeting(self, name: str = ""):
        """Speak a greeting based on time of day."""
        from datetime import datetime
        hour = datetime.now().hour

        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        if name:
            greeting += f", {name}"

        self.speak(f"{greeting}. Your CEO assistant is ready.")


class Listener:
    """Speech recognition for voice input."""

    def __init__(self, timeout: int = 10, phrase_limit: int = 30, device_index: int = None):
        """
        Initialize speech recognizer.

        Args:
            timeout: Seconds to wait for speech to start
            phrase_limit: Max seconds for a phrase
            device_index: Specific microphone index (None for default)
        """
        if sr is None:
            self.recognizer = None
            self.microphone = None
            return

        self.recognizer = sr.Recognizer()

        # Use specific device or default
        if device_index is not None:
            self.microphone = sr.Microphone(device_index=device_index)
        else:
            self.microphone = sr.Microphone()

        self.timeout = timeout
        self.phrase_limit = phrase_limit

        # Configure recognizer for better detection
        self.recognizer.energy_threshold = 300  # Lower = more sensitive
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Seconds of silence to consider phrase complete

        # Adjust for ambient noise on init
        print("Calibrating microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microphone ready.")

    def listen(self, prompt: Optional[str] = None) -> Optional[str]:
        """
        Listen for speech and return transcription using Groq Whisper.

        Args:
            prompt: Optional prompt to speak before listening

        Returns:
            Transcribed text or None if failed
        """
        if not self.recognizer:
            print("[Listener disabled] Type your response: ", end="")
            return input().strip()

        if prompt:
            voice = get_voice()
            voice.speak(prompt)

        print("\n>>> Listening... (speak now)")

        try:
            with self.microphone as source:
                # Brief noise adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)

                audio = self.recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_limit
                )

            print("Processing speech...")

            # Use Groq Whisper for transcription
            if Groq and os.environ.get("GROQ_API_KEY"):
                try:
                    text = self._transcribe_with_whisper(audio)
                    if text:
                        print(f"You said: {text}")
                        return text
                except Exception as e:
                    print(f"Whisper error: {e}")

            # Fallback to Google
            try:
                text = self.recognizer.recognize_google(audio, language="en-US")
                print(f"You said: {text}")
                return text
            except sr.UnknownValueError:
                print("Could not understand. Try speaking more clearly.")
                return None
            except sr.RequestError as e:
                print(f"Speech API error: {e}")
                return None

        except sr.WaitTimeoutError:
            print("No speech detected. Please try again.")
            return None

        except Exception as e:
            print(f"Error: {e}")
            return None

    def _transcribe_with_whisper(self, audio) -> Optional[str]:
        """Transcribe audio using Groq Whisper API."""
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio.get_wav_data())
            audio_path = f.name

        try:
            client = Groq()
            with open(audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=(audio_path, audio_file.read()),
                    model="whisper-large-v3",
                    language="en",
                    response_format="text"
                )
            return transcription.strip() if transcription else None
        finally:
            # Cleanup temp file
            try:
                os.unlink(audio_path)
            except:
                pass

    def listen_continuous(self, callback: Callable[[str], None], stop_phrase: str = "stop listening"):
        """
        Continuously listen and call callback with transcribed text.

        Args:
            callback: Function to call with each transcription
            stop_phrase: Phrase that stops listening
        """
        if not self.recognizer:
            print("[Listener disabled]")
            return

        print(f"Continuous listening started. Say '{stop_phrase}' to stop.")

        while True:
            text = self.listen()
            if text:
                if stop_phrase.lower() in text.lower():
                    print("Stopping continuous listen.")
                    break
                callback(text)


class Conversation:
    """Voice conversation handler."""

    def __init__(self, voice: Optional[Voice] = None, listener: Optional[Listener] = None):
        self.voice = voice or Voice()
        self.listener = listener or Listener()
        self.context = []  # Conversation history

    def say(self, text: str):
        """Say something and add to context."""
        self.context.append({"role": "assistant", "content": text})
        self.voice.speak(text)

    def ask(self, question: str) -> Optional[str]:
        """Ask a question and get voice response."""
        self.context.append({"role": "assistant", "content": question})
        self.voice.speak(question)

        response = self.listener.listen()
        if response:
            self.context.append({"role": "user", "content": response})
        return response

    def listen_and_respond(self, responder: Callable[[str, list], str]):
        """
        Listen for input and generate response using provided function.

        Args:
            responder: Function that takes (user_input, context) and returns response
        """
        user_input = self.listener.listen()
        if user_input:
            self.context.append({"role": "user", "content": user_input})
            response = responder(user_input, self.context)
            self.say(response)
            return response
        return None


# Global instances
_voice = None
_listener = None


def get_voice() -> Voice:
    """Get or create global voice instance."""
    global _voice
    if _voice is None:
        _voice = Voice()
    return _voice


def get_listener() -> Listener:
    """Get or create global listener instance."""
    global _listener
    if _listener is None:
        _listener = Listener()
    return _listener


def speak(text: str, block: bool = True):
    """Convenience function to speak text."""
    get_voice().speak(text, block)


def speak_brief(brief: str):
    """Convenience function to speak a brief."""
    get_voice().speak_brief(brief)


def listen(prompt: Optional[str] = None) -> Optional[str]:
    """Convenience function to listen for speech."""
    return get_listener().listen(prompt)


if __name__ == "__main__":
    # Test
    v = Voice()
    print("Available voices:")
    for voice in v.list_voices():
        print(f"  {voice['id']}: {voice['name']}")

    print("\nTesting female voice...")
    v.speak("Hello, I am your CEO assistant. I am here to help you stay focused and productive.")

    print("\nTesting listener...")
    l = Listener()
    response = l.listen("What would you like to work on today?")
    if response:
        v.speak(f"Got it. You want to work on: {response}")
