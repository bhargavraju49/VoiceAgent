"""Test the voice bridge functionality - speech to text to search to speech."""

import sys
import time
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))


def test_voice_bridge_workflow():
    """Test the complete voice workflow without requiring actual audio."""
    print("🎤 Testing Voice Bridge Workflow")
    print("=" * 50)
    
    try:
        # Import the voice tools and search
        from rag_agent.tools.voice_tools import text_to_speech_tool
        from rag_agent.tools.search_tools import search_documents
        from google.adk.tools import ToolContext
        
        # Create mock ToolContext
        class MockToolContext:
            pass
        
        tool_context = MockToolContext()
        
        # Simulate voice workflow steps
        print("\n🔄 Simulating Voice Bridge Workflow:")
        print("1. User speaks: 'How do I contact Halifax for a claim?'")
        
        # Step 1: Simulate speech-to-text (we'll use direct text for testing)
        simulated_speech_text = "How do I contact Halifax for a claim?"
        print(f"2. Speech-to-text result: '{simulated_speech_text}'")
        
        # Step 2: Use the same search functionality as text agent
        print("3. Searching policy documents...")
        start_time = time.time()
        search_result = search_documents(simulated_speech_text, tool_context)
        search_time = time.time() - start_time
        
        print(f"   Status: {search_result['status']}")
        print(f"   Search time: {search_time:.3f} seconds")
        print(f"   Sources: {search_result.get('sources', [])}")
        
        if search_result['status'] == 'success':
            answer = search_result['answer']
            print(f"   Answer length: {len(answer)} characters")
            print(f"   Answer preview: {answer[:200]}...")
            
            # Step 3: Convert to speech-friendly format
            speech_friendly_answer = convert_to_speech_friendly(answer)
            print(f"4. Speech-friendly answer: {speech_friendly_answer[:200]}...")
            
            # Step 4: Convert to speech (TTS)
            print("5. Converting to speech...")
            tts_start = time.time()
            tts_result = text_to_speech_tool(speech_friendly_answer[:500])  # Limit length for demo
            tts_time = time.time() - tts_start
            
            print(f"   TTS Status: {tts_result['status']}")
            print(f"   TTS time: {tts_time:.3f} seconds")
            
            print(f"\n✅ Complete workflow time: {search_time + tts_time:.3f} seconds")
            print("🔊 Voice response would be played to user")
            
        else:
            print("❌ Search failed, voice response would be error message")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def convert_to_speech_friendly(text: str) -> str:
    """Convert text to be more speech-friendly."""
    # Replace phone numbers for better speech
    speech_text = text.replace("0345 604 6473", "zero-three-four-five, six-zero-four, six-four-seven-three")
    
    # Add speech markers
    speech_text = f"Based on your Halifax insurance policy, {speech_text}"
    
    # Add helpful ending
    if "Source:" not in speech_text:
        speech_text += " Is there anything else I can help you with regarding your insurance policy?"
    
    return speech_text


def test_multiple_voice_queries():
    """Test multiple voice queries to simulate real usage."""
    print("\n🎯 Testing Multiple Voice Queries")
    print("=" * 50)
    
    test_queries = [
        "How do I make a claim?",
        "What's the phone number for Halifax?", 
        "What does buildings insurance cover?",
        "What should I do if there's a fire?",
        "How do I contact them?"
    ]
    
    try:
        from rag_agent.tools.search_tools import search_documents
        from google.adk.tools import ToolContext
        
        class MockToolContext:
            pass
        
        tool_context = MockToolContext()
        
        total_time = 0
        successful_queries = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Voice Query: '{query}'")
            
            start_time = time.time()
            result = search_documents(query, tool_context)
            query_time = time.time() - start_time
            total_time += query_time
            
            if result['status'] == 'success':
                successful_queries += 1
                answer_preview = result['answer'][:150] + "..."
                print(f"   ✅ Found answer ({query_time:.3f}s): {answer_preview}")
                
                # Check for contact info
                if any(indicator in result['answer'].lower() for indicator in ['0345', 'contact', 'halifax', 'phone']):
                    print("   📞 Contains contact information")
            else:
                print(f"   ❌ No information found ({query_time:.3f}s)")
        
        print(f"\n📊 Summary:")
        print(f"   Successful queries: {successful_queries}/{len(test_queries)}")
        print(f"   Average response time: {total_time/len(test_queries):.3f} seconds")
        print(f"   Total time: {total_time:.3f} seconds")
        
        if successful_queries >= len(test_queries) * 0.8:
            print("   ✅ Voice bridge system working well!")
        else:
            print("   ⚠️ Some queries failed - may need policy document improvements")
            
    except Exception as e:
        print(f"❌ Multiple query test failed: {e}")


def show_voice_bridge_architecture():
    """Show how the voice bridge architecture works."""
    print("\n🏗️ Voice Bridge Architecture")
    print("=" * 50)
    
    architecture = """
    🎤 USER SPEAKS
         ↓
    🔊 SPEECH-TO-TEXT (Whisper)
         ↓
    📝 TEXT QUERY ("How do I make a claim?")
         ↓
    🔍 SEARCH DOCUMENTS (Same as text agent)
         ↓
    📄 SEARCH RESULTS (Contact: 0345 604 6473...)
         ↓
    🗣️ SPEECH-FRIENDLY CONVERSION
         ↓
    🔊 TEXT-TO-SPEECH (pyttsx3)
         ↓
    👂 USER HEARS RESPONSE
    
    Key Benefits:
    ✅ Uses SAME search logic as text agent
    ✅ No separate voice search implementation needed
    ✅ Consistent results between text and voice
    ✅ Fast processing with offline TTS/STT
    ✅ Natural speech input/output
    """
    
    print(architecture)


if __name__ == "__main__":
    try:
        test_voice_bridge_workflow()
        test_multiple_voice_queries()
        show_voice_bridge_architecture()
        
        print("\n🎉 Voice Bridge Testing Complete!")
        print("\n📝 Next Steps:")
        print("1. Run 'adk web' to start the agent")
        print("2. Test voice mode in the ADK interface")
        print("3. The voice assistant will now use the same search as text mode")
        print("4. Responses should include contact info like '0345 604 6473'")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()