#!/usr/bin/env python3
"""Test to verify agent only uses document content"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent
INDEXED_POLICIES_DIR = ROOT_DIR / "data" / "indexed_policies"

def search_documents(query: str):
    """Search through indexed policy documents"""
    
    if not INDEXED_POLICIES_DIR.exists():
        return {
            "status": "error",
            "message": "Indexed policies directory not found.",
            "answer": "",
            "sources": [],
        }

    all_chunks = []
    for indexed_file in INDEXED_POLICIES_DIR.glob("*.json"):
        with open(indexed_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            source = data.get("source_filename", "Unknown")
            for chunk in data.get("chunks", []):
                all_chunks.append({"source": source, "content": chunk})

    # Improved keyword matching with scoring
    stop_words = {"what", "is", "the", "a", "an", "for", "this", "that", "in", "on", "at", "to", "of", "and", "or"}
    query_keywords = [word.lower() for word in query.split() if word.lower() not in stop_words]
    
    # Score chunks based on keyword matches
    scored_chunks = []
    for chunk in all_chunks:
        content_lower = chunk["content"].lower()
        matches = sum(1 for keyword in query_keywords if keyword in content_lower)
        if matches > 0:
            scored_chunks.append({
                "chunk": chunk,
                "score": matches
            })
    
    # Sort by score and get top chunks
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    relevant_chunks = [item["chunk"] for item in scored_chunks[:5]]

    if not relevant_chunks:
        return {
            "status": "not_found",
            "answer": "No information found for the query in the indexed policy documents.",
            "sources": [],
            "message": "The search did not find any matching content in the available insurance policies."
        }

    answer = " ".join([chunk["content"] for chunk in relevant_chunks])
    sources = sorted(list(set(chunk["source"] for chunk in relevant_chunks)))

    return {
        "status": "success",
        "answer": answer,
        "sources": sources,
        "message": f"Found information in {len(sources)} policy document(s)."
    }


def test_queries():
    """Test various queries"""
    
    test_cases = [
        ("claims process", True, "Should find claims info"),
        ("age limit", True, "Should find age limit info"),
        ("what is blockchain", False, "Should NOT find - not in docs"),
        ("tell me about artificial intelligence", False, "Should NOT find - not in docs"),
        ("loan coverage", True, "Should find loan info"),
    ]
    
    print("\n" + "="*70)
    print("TESTING DOCUMENT-ONLY SEARCH")
    print("="*70)
    
    for query, should_find, description in test_cases:
        print(f"\n📋 Test: {description}")
        print(f"Query: '{query}'")
        
        result = search_documents(query)
        
        found = result["status"] == "success"
        status_icon = "✅" if found == should_find else "❌"
        
        print(f"{status_icon} Status: {result['status']}")
        print(f"Message: {result.get('message', 'N/A')}")
        
        if found:
            print(f"Sources: {result['sources']}")
            print(f"Answer preview: {result['answer'][:100]}...")
        else:
            print(f"Answer: {result['answer']}")
        
        # Verify expected behavior
        if found == should_find:
            print("✅ PASS: Behavior matches expectation")
        else:
            print("❌ FAIL: Unexpected behavior!")
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("✅ Agent should ONLY answer from indexed documents")
    print("✅ Agent should return 'not found' for queries outside documents")
    print("✅ Agent should NEVER use general knowledge")


if __name__ == "__main__":
    test_queries()
