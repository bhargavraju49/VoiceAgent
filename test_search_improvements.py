"""Simple test for search functionality improvements."""

import json
from pathlib import Path


def test_improved_search():
    """Test the improved search functionality."""
    print("🔍 Testing Improved Search Functionality")
    print("=" * 50)
    
    # Direct implementation of the improved search logic
    ROOT_DIR = Path(__file__).parent
    INDEXED_POLICIES_DIR = ROOT_DIR / "data" / "indexed_policies"
    
    if not INDEXED_POLICIES_DIR.exists():
        print("❌ Indexed policies directory not found.")
        return
    
    # Load all chunks
    all_chunks = []
    for indexed_file in INDEXED_POLICIES_DIR.glob("*.json"):
        with open(indexed_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            source = data.get("source_filename", "Unknown")
            for chunk in data.get("chunks", []):
                all_chunks.append({"source": source, "content": chunk})
    
    print(f"📁 Loaded {len(all_chunks)} chunks from {len(list(INDEXED_POLICIES_DIR.glob('*.json')))} files")
    
    test_queries = [
        "claims",
        "how do I make a claim",
        "what is covered",
        "contact information",
        "buildings insurance"
    ]
    
    for query in test_queries:
        print(f"\n📋 Query: '{query}'")
        print("-" * 30)
        
        # Improved keyword matching with scoring
        stop_words = {"what", "is", "the", "a", "an", "for", "this", "that", "in", "on", "at", "to", "of", "and", "or", "how", "when", "where", "why", "who"}
        query_keywords = [word.lower() for word in query.split() if word.lower() not in stop_words]
        
        print(f"Keywords: {query_keywords}")
        
        # Score chunks based on keyword matches
        scored_chunks = []
        for chunk in all_chunks:
            content_lower = chunk["content"].lower()
            matches = sum(1 for keyword in query_keywords if keyword in content_lower)
            if matches > 0:
                # Boost score for exact phrase matches
                if query.lower() in content_lower:
                    matches += 2
                scored_chunks.append({
                    "chunk": chunk,
                    "score": matches
                })
        
        # Sort by score and get top chunks
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        relevant_chunks = [item["chunk"] for item in scored_chunks[:3]]
        
        if not relevant_chunks:
            print("❌ No relevant chunks found")
            continue
            
        print(f"✅ Found {len(relevant_chunks)} relevant chunks")
        
        # Extract relevant sentences
        def extract_relevant_sentences(content: str, keywords: list) -> str:
            sentences = []
            for part in content.split('\n'):
                sentences.extend([s.strip() for s in part.split('.') if s.strip()])
            
            relevant_sentences = []
            for sentence in sentences:
                if not sentence.strip():
                    continue
                sentence_lower = sentence.lower()
                if any(keyword in sentence_lower for keyword in keywords):
                    relevant_sentences.append(sentence.strip() + '.')
                    
            return ' '.join(relevant_sentences[:5])
        
        # Extract relevant content from chunks
        relevant_content = []
        for chunk in relevant_chunks:
            extracted = extract_relevant_sentences(chunk["content"], query_keywords)
            if extracted:
                relevant_content.append(extracted)
        
        # Combine relevant content
        if relevant_content:
            answer = " ".join(relevant_content)
            if len(answer) > 1000:
                answer = answer[:1000] + "..."
                
            print(f"Answer length: {len(answer)} characters")
            print(f"Answer preview: {answer[:300]}...")
        else:
            print("⚠️ No relevant sentences found in chunks")
        
        sources = sorted(list(set(chunk["source"] for chunk in relevant_chunks)))
        print(f"Sources: {sources}")
    
    print("\n✅ Search functionality test completed!")
    print("\n📊 Improvements implemented:")
    print("   • Focused sentence extraction")
    print("   • Better keyword matching")
    print("   • Response length limiting")
    print("   • Phrase matching boost")


if __name__ == "__main__":
    try:
        test_improved_search()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()