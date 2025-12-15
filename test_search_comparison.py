#!/usr/bin/env python3
"""
Compare the two search functions to show the difference in quality.
"""

from rag_agent.tools.faiss_search_tools import faiss_search_documents_impl
from rag_agent.tools.search_tools import search_documents
from google.adk.tools import ToolContext

def compare_search_methods():
    """Compare basic search vs FAISS search for the same queries."""
    
    test_queries = [
        "Are termites covered in my insurance?",
        "How to make a complaint?",
        "What is the phone number?",
        "How do I make a claim?",
        "What is buildings insurance?"
    ]
    
    print("🔍 SEARCH METHOD COMPARISON")
    print("="*80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*20} QUERY {i}: {query} {'='*20}")
        
        # Test basic search
        print("\n📝 BASIC KEYWORD SEARCH (search_documents):")
        print("-" * 50)
        try:
            basic_result = search_documents(query, ToolContext())
            print(f"Status: {basic_result.get('status', 'unknown')}")
            print(f"Message: {basic_result.get('message', 'No message')[:200]}...")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        # Test FAISS search
        print(f"\n🎯 FAISS VECTOR SEARCH (faiss_search_documents_impl):")
        print("-" * 50)
        try:
            faiss_result = faiss_search_documents_impl(query)
            print(f"Status: {faiss_result.get('status', 'unknown')}")
            print(f"Message: {faiss_result.get('message', 'No message')}")
            if faiss_result.get('results'):
                print(f"Results found: {len(faiss_result['results'])}")
                print(f"Top score: {faiss_result['results'][0].get('score', 'N/A'):.3f}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    compare_search_methods()