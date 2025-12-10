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
Tools for file handling in the Insurance Policy RAG agent.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

from google.adk.tools import FunctionTool, ToolContext

# Define paths
ROOT_DIR = Path(__file__).parent.parent
INDEXED_POLICIES_DIR = ROOT_DIR / "data" / "indexed_policies"
FILE_STORE_CONFIG = ROOT_DIR / "file_store_config.json"


def get_indexed_policies() -> List[str]:
    """Get the list of already indexed policy files."""
    if not FILE_STORE_CONFIG.exists():
        return []
    with open(FILE_STORE_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)
        return config.get("indexed_files", [])


def list_available_policies(tool_context: ToolContext) -> Dict[str, Any]:
    """
    List the insurance policies that have been indexed.

    Args:
        tool_context: The tool context (automatically provided by ADK).

    Returns:
        A dictionary containing the list of indexed policy filenames.
    """
    indexed_policies = get_indexed_policies()
    if not indexed_policies:
        return {"status": "success", "policies": "No insurance policies have been indexed yet."}
    return {"status": "success", "policies": indexed_policies}


def process_file_for_indexing(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Process a file for indexing.

    This is a placeholder function. In a real application, this function
    would parse the file (e.g., a PDF), split it into chunks, and potentially
    generate embeddings. For this example, we'll just simulate this process.

    Args:
        file_content: The binary content of the file.
        filename: The name of the file.

    Returns:
        A dictionary representing the structured, indexed data.
    """
    # In a real implementation, you would use a library like PyPDF2 or pdfplumber
    # to extract text from the PDF content.
    # For this example, we'll just create dummy chunks.
    num_chars = len(file_content)
    return {
        "source_filename": filename,
        "content_summary": f"This is a summary for {filename} ({num_chars} bytes).",
        "chunks": [
            f"This is the first chunk of content from {filename}.",
            f"This is the second chunk, discussing policy details from {filename}.",
            f"This is the final chunk of the document {filename}.",
        ],
    }


# Create the FunctionTools
list_files_tool = FunctionTool(list_available_policies)

file_processing_tool = FunctionTool(process_file_for_indexing)

