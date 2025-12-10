"""Test enhanced search with real policy document."""

import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

def test_enhanced_search_directly():
    """Test the enhanced search functionality directly."""
    from rag_agent.tools.search_tools import search_documents
    from google.adk.tools import ToolContext
    
    print("🔍 Testing Enhanced Search with Real Policy")
    print("=" * 60)
    
    # Test specific queries that were problematic
    test_queries = [
        "how to contact for claims",
        "phone number for claims", 
        "contact information",
        "0345",
        "Halifax phone",
        "call them",
        "reach them"
    ]
    
    for query in test_queries:
        print(f"\n📋 Testing Query: '{query}'")
        print("-" * 40)
        
        try:
            # Create mock ToolContext - we'll handle the missing parameter differently
            class MockToolContext:
                pass
            
            result = search_documents(query, MockToolContext())
            
            print(f"✅ Status: {result['status']}")
            
            if result['status'] == 'success':
                answer = result['answer']
                sources = result['sources']
                
                print(f"📄 Sources: {sources}")
                print(f"📝 Answer length: {len(answer)} characters")
                print(f"💬 Answer: {answer[:500]}...")
                
                # Check if answer contains contact info
                contact_indicators = ['0345', 'phone', 'call', 'contact', 'Halifax']
                found_indicators = [ind for ind in contact_indicators if ind.lower() in answer.lower()]
                if found_indicators:
                    print(f"✅ Found contact indicators: {found_indicators}")
                else:
                    print("⚠️ No specific contact information found")
            else:
                print(f"❌ Search failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n📊 Test Summary:")
    print("The enhanced search should now:")
    print("   ✓ Extract relevant sentences about contact and claims")
    print("   ✓ Prioritize content with phone numbers and contact info")
    print("   ✓ Provide more context for contact queries") 
    print("   ✓ Limit response length while preserving important details")


def show_policy_content_sample():
    """Show what content is available in the policy files."""
    print("\n📄 Available Policy Content Sample")
    print("=" * 60)
    
    from pathlib import Path
    import json
    
    indexed_dir = Path(__file__).parent / "data" / "indexed_policies"
    
    if indexed_dir.exists():
        json_files = list(indexed_dir.glob("*.json"))
        print(f"Found {len(json_files)} indexed policy files")
        
        for json_file in json_files[:1]:  # Show first file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                source = data.get("source_filename", "Unknown")
                chunks = data.get("chunks", [])
                
                print(f"\n📋 File: {source}")
                print(f"📊 Total chunks: {len(chunks)}")
                
                # Look for chunks that might contain contact info
                contact_chunks = []
                for i, chunk in enumerate(chunks):
                    if any(word in chunk.lower() for word in ['phone', 'contact', 'call', '0345', 'halifax']):
                        contact_chunks.append((i, chunk))
                
                print(f"🔍 Chunks with potential contact info: {len(contact_chunks)}")
                
                if contact_chunks:
                    for i, chunk in contact_chunks[:2]:  # Show first 2
                        print(f"\n--- Chunk {i} (first 300 chars) ---")
                        print(chunk[:300] + "...")
    else:
        print("❌ No indexed policies directory found")


if __name__ == "__main__":
    try:
        show_policy_content_sample()
        test_enhanced_search_directly()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()