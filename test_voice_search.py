#!/usr/bin/env python3
"""
Test script for voice-optimized search functionality.
"""

from rag_agent.tools.faiss_search_tools import faiss_search_documents_impl

def test_voice_search():
    """Test the voice-optimized search with common queries."""
    
    test_queries = [
        "How to make complaints on legal expenses",
        "How do I make a claim",
        "What is the phone number for customer service",
        "How to contact Halifax insurance"
    ]
    
    print("=== Voice-Optimized Search Test ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 50)
        
        try:
            result = faiss_search_documents_impl(query)
            
            if result['status'] == 'success':
                print("✅ Voice Response:")
                print(f"   {result['message']}")
                print(f"\n📊 Found {len(result['results'])} results")
                
                # Show first result details
                if result['results']:
                    first_result = result['results'][0]
                    print(f"📄 Best Match Score: {first_result['score']:.3f}")
                    print(f"📁 Source: {first_result['source']}")
            else:
                print(f"❌ Error: {result['message']}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        print("\n" + "="*80 + "\n")

def test_content_cleaning():
    """Test the content cleaning function with sample text."""
    
    sample_content = "25 How to make a complaint 26 Your Legal Expenses cover 27 Words and phrases with a special meaning 28 Summary of Legal Expenses cover 30 How to make a claim 31 Claims procedure and conditions"
    
    print("=== Content Cleaning Test ===\n")
    print("Original Content:")
    print(f"   {sample_content}")
    print()
    
    # Simulate the cleaning process
    import re
    
    # Remove page references and section numbers
    cleaned = re.sub(r'\b(?:Pages?\s+\d+(?:-\d+)?(?:\s+apply)?|Section\s+\d+|Page\s+\d+)', '', sample_content, flags=re.IGNORECASE)
    
    # Remove standalone numbers that look like page/section references
    cleaned = re.sub(r'\b\d+\s+(?=How to|What|When|Where|Why|Your|Legal)', '', cleaned)
    
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    print("Cleaned Content:")
    print(f"   {cleaned.strip()}")

if __name__ == "__main__":
    print("Testing Voice-Optimized Insurance Policy Search\n")
    
    # Test content cleaning first
    test_content_cleaning()
    print("\n" + "="*80 + "\n")
    
    # Test actual search
    test_voice_search()