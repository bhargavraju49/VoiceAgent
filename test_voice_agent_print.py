#!/usr/bin/env python3
"""
Test script to demonstrate voice agent functionality with detailed print output.
Shows exactly what the search results are and what the agent is saying.
"""

from rag_agent.tools.faiss_search_tools import faiss_search_documents_impl
import json

def format_output(response):
    """Format the response for pretty printing."""
    print("="*80)
    print("VOICE AGENT SEARCH RESULTS")
    print("="*80)
    
    print(f"Query: {response['query']}")
    print(f"Status: {response['status']}")
    print()
    
    if response.get('results'):
        print(f"Number of Results Found: {len(response['results'])}")
        print("-"*50)
        
        for i, result in enumerate(response['results'], 1):
            print(f"Result {i}:")
            print(f"  Score: {result['score']:.6f}")
            print(f"  Source: {result['source']}")
            print(f"  Type: {result['type']}")
            print(f"  Content: {result['content']}")
            print()
    else:
        print("No search results found")
    
    print("="*80)
    print("AGENT RESPONSE (What the agent is saying):")
    print("="*80)
    print(f"Message: {response['message']}")
    print("="*80)
    print()

def test_termites_query():
    """Test the termites coverage query."""
    print("Testing termites coverage query...")
    
    query = "Are termites covered in my insurance?"
    
    try:
        response = faiss_search_documents_impl(query=query)
        format_output(response)
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_multiple_queries():
    """Test multiple different queries to show variety of responses."""
    
    queries = [
        "Are termites covered in my insurance?",
        "How to make a complaint about legal expenses?",
        "How do I make a claim?",
        "What is the customer service phone number?",
        "What is covered under buildings insurance?",
        "What about accidental damage coverage?"
    ]
    
    print("TESTING MULTIPLE VOICE AGENT QUERIES")
    print("="*80)
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*20} QUERY {i} {'='*20}")
        try:
            response = faiss_search_documents_impl(query=query)
            
            # Show compact results first
            print(f"Query: {query}")
            print(f"Status: {response['status']}")
            print(f"Results found: {len(response.get('results', []))}")
            
            if response.get('results'):
                top_score = response['results'][0]['score']
                print(f"Top result score: {top_score:.6f}")
            
            print(f"\n🗣️ AGENT SAYS: {response['message']}")
            
        except Exception as e:
            print(f"Error for query '{query}': {str(e)}")

def test_voice_agent_print_demo():
    """Main demo function showing the exact format you requested."""
    
    print("VOICE AGENT DEMO - EXACT FORMAT")
    print("="*80)
    
    # Test the specific termites query as shown in your example
    query = "Are termites covered in my insurance?"
    
    print(f'response = default_api.faiss_search_documents_impl(query="{query}")')
    print('print(response)')
    print()
    
    response = faiss_search_documents_impl(query=query)
    
    print("Outcome: OUTCOME_OK")
    print(f"Output: {json.dumps(response, indent=2)}")
    print()
    
    print("="*80)
    print("WHAT THE AGENT IS SAYING:")
    print("="*80)
    print(f"Agent Response: {response['message']}")
    print()
    
    # Show voice-friendly format
    print("="*80)
    print("VOICE-FRIENDLY FORMAT:")
    print("="*80)
    print("🎤 User asked:", query)
    print("🤖 Agent responds:", response['message'])
    print()
    
    if response.get('results'):
        print("📊 SEARCH DETAILS:")
        for i, result in enumerate(response['results'], 1):
            print(f"  {i}. Score: {result['score']:.3f} | Source: {result['source']}")
            print(f"     Content: {result['content'][:100]}...")
            print()

if __name__ == "__main__":
    # Run the main demo
    test_voice_agent_print_demo()
    
    # Also run additional tests
    print("\n" + "="*80)
    print("ADDITIONAL QUERIES TEST")
    test_multiple_queries()