# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Search tool - Searches pre-indexed insurance policy documents.

This tool searches for information within the JSON files located in the
`data/indexed_policies` directory.
"""

import json
from pathlib import Path
from typing import Dict, Any

from google.adk.tools import FunctionTool, ToolContext

# Define paths
ROOT_DIR = Path(__file__).parent.parent.parent
INDEXED_POLICIES_DIR = ROOT_DIR / "data" / "indexed_policies"


def search_documents(query: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Search through pre-indexed insurance policy documents.

    This tool performs a simple text search through the JSON files in the
    `data/indexed_policies` directory.

    Args:
        query: The search query or question.
        tool_context: The tool context (automatically provided by ADK).

    Returns:
        A dictionary containing the search results.
    """
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
    # Extract keywords from query (remove common words)
    stop_words = {"what", "is", "the", "a", "an", "for", "this", "that", "in", "on", "at", "to", "of", "and", "or", "how", "when", "where", "why", "who"}
    query_keywords = [word.lower() for word in query.split() if word.lower() not in stop_words]
    
    # Score chunks based on keyword matches
    scored_chunks = []
    for chunk in all_chunks:
        content_lower = chunk["content"].lower()
        # Count how many query keywords appear in the chunk
        matches = sum(1 for keyword in query_keywords if keyword in content_lower)
        if matches > 0:
            # Also boost score for exact phrase matches
            if query.lower() in content_lower:
                matches += 2
            scored_chunks.append({
                "chunk": chunk,
                "score": matches
            })
    
    # Sort by score (highest first) and get top chunks
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    relevant_chunks = [item["chunk"] for item in scored_chunks[:3]]  # Top 3 chunks only

    if not relevant_chunks:
        return {
            "status": "not_found",
            "answer": "No information found for the query in the indexed policy documents.",
            "sources": [],
            "message": "The search did not find any matching content in the available insurance policies."
        }

    # Extract relevant sentences instead of returning entire chunks
    def extract_relevant_sentences(content: str, keywords: list, query: str) -> str:
        """Extract sentences that contain the query keywords with enhanced context."""
        # Split by periods and also by newlines for better sentence detection
        sentences = []
        for part in content.split('\n'):
            sentences.extend([s.strip() for s in part.split('.') if s.strip()])
        
        relevant_sentences = []
        
        # First pass: sentences with exact keyword matches
        for sentence in sentences:
            if not sentence.strip():
                continue
            sentence_lower = sentence.lower()
            # Check if sentence contains any of the keywords
            if any(keyword in sentence_lower for keyword in keywords):
                relevant_sentences.append(sentence.strip() + '.')
        
        # Second pass: for contact/phone queries, look for numbers and contact info
        if any(word in query.lower() for word in ['contact', 'phone', 'call', 'reach', 'number']):
            phone_pattern = r'\b\d{4}\s?\d{3}\s?\d{4}\b|\b0\d{3}\s?\d{3}\s?\d{4}\b'
            for sentence in sentences:
                if not sentence.strip():
                    continue
                # Look for phone numbers, contact words, or service mentions
                if any(word in sentence.lower() for word in ['phone', 'call', 'contact', 'service', 'reach', 'number', '0345', 'halifax']):
                    if sentence.strip() + '.' not in relevant_sentences:
                        relevant_sentences.append(sentence.strip() + '.')
        
        # Third pass: for claims, look for procedural information
        if any(word in query.lower() for word in ['claim', 'claims']):
            for sentence in sentences:
                if not sentence.strip():
                    continue
                if any(word in sentence.lower() for word in ['claim', 'contact', 'call', 'report', 'notify', 'phone', 'soon', 'immediately']):
                    if sentence.strip() + '.' not in relevant_sentences:
                        relevant_sentences.append(sentence.strip() + '.')
                        
        return ' '.join(relevant_sentences[:8])  # Increased to 8 sentences for better context
    
    # Extract relevant content from chunks
    relevant_content = []
    for chunk in relevant_chunks:
        extracted = extract_relevant_sentences(chunk["content"], query_keywords, query)
        if extracted:
            relevant_content.append(extracted)
    
    # If no relevant sentences found, fall back to contextual search
    if not relevant_content:
        best_chunk = relevant_chunks[0]["content"]
        # Take context around the keyword
        best_chunk_lower = best_chunk.lower()
        for keyword in query_keywords:
            if keyword in best_chunk_lower:
                start_idx = best_chunk_lower.find(keyword)
                # Get more context around the keyword
                start = max(0, start_idx - 300)
                end = min(len(best_chunk), start_idx + 500)
                context = best_chunk[start:end]
                relevant_content.append(context)
                break
        else:
            # Final fallback to beginning
            relevant_content.append(best_chunk[:800] + "..." if len(best_chunk) > 800 else best_chunk)
    
    # Combine relevant content
    answer = " ".join(relevant_content)
    
    # Limit total response length but allow more for important queries
    max_length = 1500 if any(word in query.lower() for word in ['contact', 'claim', 'phone', 'call']) else 1000
    if len(answer) > max_length:
        answer = answer[:max_length] + "..."
    
    sources = sorted(list(set(chunk["source"] for chunk in relevant_chunks)))

    return {
        "status": "success",
        "answer": answer,
        "sources": sources,
        "message": f"Found information in {len(sources)} policy document(s)."
    }


# Create the FunctionTool
search_tool = FunctionTool(search_documents)
