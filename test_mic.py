"""Microphone test using Groq Whisper."""

import os
import tempfile
import speech_recognition as sr

print("=== Microphone Test (Groq Whisper) ===\n")

# Check for API key - must be set in environment
if not os.environ.get("GROQ_API_KEY"):
    print("Error: GROQ_API_KEY not set")
    exit(1)

from groq import Groq

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.pause_threshold = 0.8

try:
    mic = sr.Microphone()

    print("Calibrating... stay quiet")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    print(f"Energy threshold: {recognizer.energy_threshold}")
    print("\n>>> SPEAK NOW! Say anything (10 seconds)...")

    with mic as source:
        audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)

    print("Audio captured!")

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio.get_wav_data())
        audio_path = f.name

    print(f"Saved to: {audio_path}")
    print("Transcribing with Groq Whisper...")

    # Use Groq Whisper
    client = Groq()

    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=(audio_path, audio_file.read()),
            model="whisper-large-v3",
            language="en",
            response_format="text"
        )

    print(f"\nSUCCESS! You said: '{transcription}'")

    # Cleanup
    os.unlink(audio_path)

except sr.WaitTimeoutError:
    print("\nTimeout - no speech detected")
except Exception as e:
    print(f"\nError: {type(e).__name__}: {e}")
