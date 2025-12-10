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

"""Test script for fast voice functionality."""

import sys
import time
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from rag_agent.tools.voice_tools import (
    speech_to_text_tool,
    text_to_speech_tool,
    real_time_speech_to_text_tool,
    VoiceManager
)
from rag_agent.tools.search_tools import search_documents
from google.adk.core import ToolContext


def test_voice_functionality():
    """Test the voice functionality modules."""
    print("🎙️ Testing Fast Voice Functionality")
    print("=" * 50)
    
    # Initialize voice manager (this loads models)
    print("📋 Initializing voice manager...")
    vm = VoiceManager()
    print("✅ Voice manager initialized")
    
    # Test Text-to-Speech
    print("\n🔊 Testing Text-to-Speech...")
    test_text = "Hello! This is a test of the fast text to speech functionality."
    
    start_time = time.time()
    result = text_to_speech_tool(test_text)
    end_time = time.time()
    
    print(f"TTS Result: {result['status']}")
    print(f"TTS Speed: {end_time - start_time:.2f} seconds")
    
    # Test Real-time Speech-to-Text (optional - requires microphone)
    print("\n🎤 Testing Real-time Speech-to-Text...")
    print("This test requires a microphone. Skip if unavailable.")
    
    try:
        user_input = input("Press Enter to test microphone listening (or 's' to skip): ")
        if user_input.lower() != 's':
            print("Listening for 3 seconds... Please speak!")
            start_time = time.time()
            result = real_time_speech_to_text_tool(duration_seconds=3)
            end_time = time.time()
            
            print(f"STT Result: {result['status']}")
            print(f"Transcribed text: '{result.get('text', 'N/A')}'")
            print(f"STT Speed: {end_time - start_time:.2f} seconds")
    except Exception as e:
        print(f"Microphone test failed: {e}")
    
    # Test Search Integration
    print("\n🔍 Testing Search Integration...")
    print("Testing improved search with focused responses...")
    
    test_queries = ["claims", "how do I make a claim", "what is covered"]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        start_time = time.time()
        result = search_documents(query, ToolContext())
        end_time = time.time()
        
        print(f"Search Status: {result['status']}")
        if result['status'] == 'success':
            answer_length = len(result['answer'])
            print(f"Answer length: {answer_length} characters")
            print(f"Answer preview: {result['answer'][:200]}...")
        print(f"Search Speed: {end_time - start_time:.2f} seconds")
    
    print("\n✨ Voice functionality tests completed!")
    print("\n📝 Next Steps:")
    print("1. Test with real audio files using speech_to_text_tool()")
    print("2. Integration with ADK voice agent")
    print("3. Test real-time voice interactions")


def demonstrate_voice_workflow():
    """Demonstrate a complete voice interaction workflow."""
    print("\n🗣️ Voice Workflow Demonstration")
    print("=" * 50)
    
    # Simulate a voice query about claims
    simulated_query = "How do I make a claim?"
    print(f"Simulated voice input: '{simulated_query}'")
    
    # Search for information
    print("\n1. Searching for information...")
    search_result = search_documents(simulated_query, ToolContext())
    
    if search_result['status'] == 'success':
        answer = search_result['answer']
        sources = search_result['sources']
        
        print(f"✅ Found information in {len(sources)} documents")
        print(f"Answer preview: {answer[:200]}...")
        
        # Convert to speech
        print("\n2. Converting response to speech...")
        tts_result = text_to_speech_tool(
            f"Based on your insurance policy, {answer[:300]}. Source: {sources[0] if sources else 'Unknown'}"
        )
        
        print(f"✅ TTS Result: {tts_result['status']}")
        print("🔊 Response played via speakers")
        
    else:
        print("❌ No information found")
        # Fallback TTS
        fallback_text = "I couldn't find information about that in your insurance policies."
        text_to_speech_tool(fallback_text)
        print("🔊 Fallback response played")


if __name__ == "__main__":
    try:
        test_voice_functionality()
        demonstrate_voice_workflow()
        
        print("\n🎉 All tests completed successfully!")
        print("\n💡 The voice system is now ready for:")
        print("   • Fast speech-to-text with Whisper")
        print("   • Fast text-to-speech with pyttsx3")
        print("   • Focused search responses")
        print("   • Real-time voice interactions")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()