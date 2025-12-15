#!/usr/bin/env python3
"""
Test script to check consistency of termite coverage responses.
"""

from rag_agent.tools.faiss_search_tools import faiss_search_documents_impl

def test_termite_consistency():
    """Test multiple termite-related queries to check consistency."""
    
    queries = [
        "Are termites covered in my insurance?",
        "Are termites damage covered in my insurance?",
        "Is termite damage covered?",
        "What about termite infestation?", 
        "Are insects covered in my policy?",
        "Is pest damage covered?",
        "What about vermin damage?",
        "Are woodworm covered?"
    ]
    
    print("TESTING TERMITE COVERAGE CONSISTENCY")
    print("="*80)
    
    responses = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*20} TEST {i} {'='*20}")
        try:
            response = faiss_search_documents_impl(query=query)
            
            message = response['message']
            responses.append(message)
            
            print(f"Query: {query}")
            print(f"Response: {message}")
            
        except Exception as e:
            print(f"Error for query '{query}': {str(e)}")
            responses.append(f"ERROR: {str(e)}")
    
    # Check consistency
    print(f"\n{'='*20} CONSISTENCY CHECK {'='*20}")
    unique_responses = list(set(responses))
    
    print(f"Number of unique responses: {len(unique_responses)}")
    
    if len(unique_responses) == 1:
        print("✅ CONSISTENT! All responses are identical:")
        print(f"   {unique_responses[0]}")
    else:
        print("❌ INCONSISTENT! Different responses found:")
        for i, resp in enumerate(unique_responses, 1):
            print(f"   {i}. {resp}")

if __name__ == "__main__":
    test_termite_consistency()