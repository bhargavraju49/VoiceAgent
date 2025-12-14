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

"""Search Assistant Agent - Answers questions about insurance policies."""

from google.adk.agents import LlmAgent
from ..tools.search_tools import search_tool
try:
    from ..tools.faiss_search_tools import faiss_search_documents, faiss_index_documents
    VECTOR_SEARCH_AVAILABLE = True
    VECTOR_TYPE = "FAISS"
except ImportError as e:
    try:
        from ..tools.vector_search_tools import enhanced_search_tool, index_documents_tool
        VECTOR_SEARCH_AVAILABLE = True
        VECTOR_TYPE = "ChromaDB"
        faiss_search_documents = enhanced_search_tool
        faiss_index_documents = index_documents_tool
    except ImportError as e2:
        print(f"No vector search available: FAISS={e}, ChromaDB={e2}")
        faiss_search_documents = None
        faiss_index_documents = None
        VECTOR_SEARCH_AVAILABLE = False
        VECTOR_TYPE = None


def create_search_assistant_agent(llm=None) -> LlmAgent:
    """
    Creates the Search Assistant agent.

    This agent is responsible for answering questions based on the content
    of the indexed insurance policies.
    """
    # Determine available tools based on imports
    if VECTOR_SEARCH_AVAILABLE:
        tools_description = f"""
    **Your Tools:**
    1. `search_documents`: Traditional keyword search through indexed policies
    2. `faiss_search_documents`: Advanced semantic search using {VECTOR_TYPE} vector database
    3. `faiss_index_documents`: Index new policy documents into vector database
    
    **Search Strategy:**
    1. **For specific questions** (claims, contact, coverage): Try `faiss_search_documents` first for better semantic understanding
    2. **If vector search fails or limited results**: Fall back to `search_documents`  
    3. **For document indexing requests**: Use `faiss_index_documents`"""
    else:
        tools_description = """
    **Your Tool:**
    1. `search_documents`: Enhanced keyword search through indexed policies (vector search unavailable)
    
    **Search Strategy:**
    1. Use `search_documents` for all queries with enhanced keyword matching"""
    
    search_assistant_prompt = f"""
    You are an insurance policy search assistant. Use the search tools to answer questions. Only answer from search results. Be brief and clear. If no answer is found, say so.
    """
    # Determine tools based on availability
    tools = [search_tool]
    if VECTOR_SEARCH_AVAILABLE:
        tools.extend([faiss_search_documents, faiss_index_documents])
        description = f"Enhanced search agent with {VECTOR_TYPE} vector database and traditional search capabilities."
    else:
        description = "Enhanced search agent with improved contact and claims search."
    
    return LlmAgent(
        name="SearchAssistantAgent",
        model="gemini-2.0-flash-exp",
        instruction=search_assistant_prompt,
        description=description,
        tools=tools,
    )
