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
    stop_words = {"what", "is", "the", "a", "an", "for", "this", "that", "in", "on", "at", "to", "of", "and", "or"}
    query_keywords = [word.lower() for word in query.split() if word.lower() not in stop_words]
    
    # Score chunks based on keyword matches
    scored_chunks = []
    for chunk in all_chunks:
        content_lower = chunk["content"].lower()
        # Count how many query keywords appear in the chunk
        matches = sum(1 for keyword in query_keywords if keyword in content_lower)
        if matches > 0:
            scored_chunks.append({
                "chunk": chunk,
                "score": matches
            })
    
    # Sort by score (highest first) and get top chunks
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    relevant_chunks = [item["chunk"] for item in scored_chunks[:5]]  # Top 5 chunks

    if not relevant_chunks:
        return {
            "status": "not_found",
            "answer": "No information found for the query in the indexed policy documents.",
            "sources": [],
            "message": "The search did not find any matching content in the available insurance policies."
        }

    # For simplicity, we'll combine the content of all relevant chunks
    # and list the unique sources.
    answer = " ".join([chunk["content"] for chunk in relevant_chunks])
    sources = sorted(list(set(chunk["source"] for chunk in relevant_chunks)))

    return {
        "status": "success",
        "answer": answer,
        "sources": sources,
        "message": f"Found information in {len(sources)} policy document(s)."
    }


# Create the FunctionTool
search_tool = FunctionTool(search_documents)
