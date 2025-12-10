# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Fast Voice Tools for Speech-to-Text and Text-to-Speech functionality."""

import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

import pyttsx3
import speech_recognition as sr
import whisper
from google.adk.tools import FunctionTool, ToolContext


class VoiceManager:
    """Singleton voice manager for TTS engine."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(VoiceManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.tts_engine = pyttsx3.init()
            self._configure_tts()
            self.whisper_model = None
            self.speech_recognizer = sr.Recognizer()
            self._initialized = True
    
    def _configure_tts(self):
        """Configure TTS engine for optimal performance."""
        try:
            # Set speech rate (words per minute)
            self.tts_engine.setProperty('rate', 200)  # Default is usually 200
            
            # Set volume (0.0 to 1.0)
            self.tts_engine.setProperty('volume', 0.9)
            
            # Get available voices
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer English voices
                english_voices = [v for v in voices if 'english' in v.name.lower() or 'en' in v.id.lower()]
                if english_voices:
                    self.tts_engine.setProperty('voice', english_voices[0].id)
                else:
                    self.tts_engine.setProperty('voice', voices[0].id)
        except Exception as e:
            print(f"Warning: TTS configuration failed: {e}")
    
    def get_whisper_model(self, model_size: str = "base"):
        """Lazy load Whisper model."""
        if self.whisper_model is None:
            self.whisper_model = whisper.load_model(model_size)
        return self.whisper_model


# Global voice manager instance
voice_manager = VoiceManager()


def speech_to_text_tool(audio_file_path: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Convert speech from audio file to text using Whisper.
    
    Args:
        audio_file_path: Path to the audio file to transcribe
        tool_context: Tool context (automatically provided by ADK)
    
    Returns:
        Dictionary with transcription results
    """
    try:
        # Validate file exists
        if not Path(audio_file_path).exists():
            return {
                "status": "error",
                "message": f"Audio file not found: {audio_file_path}",
                "text": ""
            }
        
        # Load and transcribe with Whisper
        model = voice_manager.get_whisper_model("base")  # Fast base model
        result = model.transcribe(audio_file_path)
        
        transcribed_text = result["text"].strip()
        
        return {
            "status": "success",
            "message": "Speech successfully transcribed to text",
            "text": transcribed_text,
            "language": result.get("language", "unknown"),
            "confidence": "high"  # Whisper doesn't provide confidence scores
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Speech-to-text conversion failed: {str(e)}",
            "text": ""
        }


def text_to_speech_tool(text: str, output_file: Optional[str] = None, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Convert text to speech using pyttsx3.
    
    Args:
        text: Text to convert to speech
        output_file: Optional path to save audio file (if None, plays directly)
        tool_context: Tool context (automatically provided by ADK)
    
    Returns:
        Dictionary with conversion results
    """
    try:
        if not text.strip():
            return {
                "status": "error",
                "message": "No text provided for speech synthesis",
                "audio_file": None
            }
        
        tts_engine = voice_manager.tts_engine
        
        if output_file:
            # Save to file
            tts_engine.save_to_file(text, output_file)
            tts_engine.runAndWait()
            
            if Path(output_file).exists():
                return {
                    "status": "success",
                    "message": f"Text converted to speech and saved to {output_file}",
                    "audio_file": output_file,
                    "text": text
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to save audio file",
                    "audio_file": None
                }
        else:
            # Play directly
            tts_engine.say(text)
            tts_engine.runAndWait()
            
            return {
                "status": "success",
                "message": "Text converted to speech and played",
                "audio_file": None,
                "text": text
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Text-to-speech conversion failed: {str(e)}",
            "audio_file": None
        }


def real_time_speech_to_text_tool(duration_seconds: int = 5, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Capture real-time speech from microphone and convert to text.
    
    Args:
        duration_seconds: How long to listen for speech (default 5 seconds)
        tool_context: Tool context (automatically provided by ADK)
    
    Returns:
        Dictionary with transcription results
    """
    try:
        recognizer = voice_manager.speech_recognizer
        
        with sr.Microphone() as source:
            print(f"Listening for {duration_seconds} seconds...")
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=1)
            # Listen for speech
            audio = recognizer.listen(source, timeout=duration_seconds, phrase_time_limit=duration_seconds)
        
        # Try Google Speech Recognition first (fast and accurate)
        try:
            text = recognizer.recognize_google(audio)
            return {
                "status": "success",
                "message": "Real-time speech successfully transcribed",
                "text": text,
                "method": "google",
                "confidence": "high"
            }
        except sr.RequestError:
            # Fallback to offline recognition with Whisper
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                with open(temp_file.name, "wb") as f:
                    f.write(audio.get_wav_data())
                
                # Use Whisper for offline transcription
                model = voice_manager.get_whisper_model("base")
                result = model.transcribe(temp_file.name)
                text = result["text"].strip()
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
                return {
                    "status": "success",
                    "message": "Real-time speech transcribed using offline model",
                    "text": text,
                    "method": "whisper",
                    "confidence": "medium"
                }
                
    except sr.WaitTimeoutError:
        return {
            "status": "timeout",
            "message": f"No speech detected within {duration_seconds} seconds",
            "text": ""
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Real-time speech recognition failed: {str(e)}",
            "text": ""
        }


# Tool definitions for ADK
speech_to_text_tool_def = FunctionTool(speech_to_text_tool)
text_to_speech_tool_def = FunctionTool(text_to_speech_tool)
real_time_speech_tool_def = FunctionTool(real_time_speech_to_text_tool)

# Export all voice tools
voice_tools = [
    speech_to_text_tool_def,
    text_to_speech_tool_def,
    real_time_speech_tool_def,
]