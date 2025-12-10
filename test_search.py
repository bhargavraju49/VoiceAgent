#!/usr/bin/env python3
"""Quick test script for search functionality - standalone version"""

import json
from pathlib import Path

# Define paths
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
    
    print(f"Extracted keywords: {query_keywords}")
    
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
    
    print(f"Found {len(scored_chunks)} matching chunks")
    
    # Sort by score and get top chunks
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    relevant_chunks = [item["chunk"] for item in scored_chunks[:5]]

    if not relevant_chunks:
        return {
            "status": "success",
            "answer": "No information found for the query.",
            "sources": [],
        }

    answer = " ".join([chunk["content"] for chunk in relevant_chunks])
    sources = sorted(list(set(chunk["source"] for chunk in relevant_chunks)))

    return {"status": "success", "answer": answer, "sources": sources}


def test_search(query: str):
    """Test a search query"""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    result = search_documents(query)
    
    print(f"Status: {result['status']}")
    if result.get('sources'):
        print(f"Sources: {result['sources']}")
    print(f"\nAnswer (first 500 chars):\n{result['answer'][:500]}...")
    

if __name__ == "__main__":
    # Test the queries that weren't working
    test_search("claims")
    test_search("age limitation for this policy")
    test_search("what documents are needed for claims")
    test_search("suicide clause")
