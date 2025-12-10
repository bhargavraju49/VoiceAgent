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
Simple File Search Tool - Searches pre-indexed JSON documents.

This tool searches for information within the JSON files located in the
`data/indexed_policies` directory.
"""

import json
from pathlib import Path
from typing import Dict, Any

from google.adk.tools import FunctionTool, ToolContext

# Define paths
ROOT_DIR = Path(__file__).parent.parent
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

    # Simple keyword matching for demonstration purposes
    # A more robust solution would use a proper search algorithm (e.g., BM25)
    # or a vector-based search.
    relevant_chunks = [
        chunk
        for chunk in all_chunks
        if any(keyword.lower() in chunk["content"].lower() for keyword in query.split())
    ]

    if not relevant_chunks:
        return {
            "status": "success",
            "answer": "No information found for the query.",
            "sources": [],
        }

    # For simplicity, we'll combine the content of all relevant chunks
    # and list the unique sources.
    answer = " ".join([chunk["content"] for chunk in relevant_chunks])
    sources = sorted(list(set(chunk["source"] for chunk in relevant_chunks)))

    return {"status": "success", "answer": answer, "sources": sources}


# Create the FunctionTool
search_tool = FunctionTool(search_documents)
