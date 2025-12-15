#!/usr/bin/env python3
"""
Test the specific query that was causing issues.
"""

from rag_agent.tools.faiss_search_tools import faiss_search_documents_impl

def test_specific_query():
    """Test the specific query from the user's original issue."""
    
    query = "How to make complaints on legal expenses"
    
    print("=== Testing Specific Query ===")
    print(f"Query: {query}")
    print("-" * 50)
    
    try:
        result = faiss_search_documents_impl(query)
        
        print(f"Status: {result['status']}")
        print(f"Voice-Friendly Message:")
        print(f"   {result['message']}")
        print(f"\nNumber of results: {len(result['results'])}")
        
        if result['results']:
            print(f"\nTop result details:")
            top_result = result['results'][0]
            print(f"   Score: {top_result['score']:.3f}")
            print(f"   Source: {top_result['source']}")
            print(f"   Content preview: {top_result['content'][:200]}...")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_specific_query()