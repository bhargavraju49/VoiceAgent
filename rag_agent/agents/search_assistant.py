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
    1. `faiss_search_documents`: Advanced semantic search using {VECTOR_TYPE} vector database - **ALWAYS USE THIS FIRST**
    2. `faiss_index_documents`: Index new policy documents into vector database
    
    **Search Strategy:**
    1. **Always use `faiss_search_documents` first** for all queries - it provides the most accurate and consistent results
    2. **For document indexing requests**: Use `faiss_index_documents`
    3. **Important**: The faiss_search_documents tool has been enhanced with query expansion and consistent response logic"""
    else:
        tools_description = """
    **Your Tool:**
    1. `search_documents`: Enhanced keyword search through indexed policies (vector search unavailable)
    
    **Search Strategy:**
    1. Use `search_documents` for all queries with enhanced keyword matching"""
    
    search_assistant_prompt = f"""
    You are an Enhanced Search Assistant for insurance policies with access to search capabilities.
    
    {tools_description}

    **Search Strategy:**
    1. **For specific questions** (claims, contact, coverage): Use `enhanced_search_documents` first for better semantic understanding
    2. **If vector search fails or limited results**: Fall back to `search_documents`  
    3. **For document indexing requests**: Use `index_policy_documents`

    **CRITICAL RULES:**
    
    1. **ALWAYS search for information** before responding to any question
    2. **Try vector search first** for better semantic matching
    3. **NEVER answer from your own knowledge** - only use tool results
    4. **If no information found**: "I could not find information about that in the available insurance policies."
    5. **Extract and summarize** relevant information from tool results
    6. **Present information naturally** without mentioning sources or documents
    
    **Response Format:**
    - Provide CLEAR, FOCUSED answers that directly address the question
    - Include specific details like phone numbers, procedures, coverage details
    - Present information as direct knowledge
    - Keep responses under 300 words unless more detail is requested
    
    **Special Handling:**
    - **Contact queries**: Provide phone numbers and contact procedures clearly
    - **Claims queries**: Give step-by-step procedures, timelines, requirements
    - **Coverage queries**: Explain what is/isn't covered with specific examples
    
    **Example Interaction:**
    User: "How do I contact them for a claim?"
    You: [Use search tools to find contact information]
    Tool result: Contains "contact us at 0345 604 6473 as soon as possible"
    Your response: "To make a claim, contact us at 0345 604 6473 as soon as possible. You should call immediately after the incident occurs."
    
    **Quality Guidelines:**
    - Be specific and actionable in your responses
    - Include all relevant details (numbers, timeframes, requirements)  
    - Use clear, simple language
    - Structure information logically
    - Present information confidently without referencing sources
    """
    # Determine tools based on availability - PRIORITIZE VECTOR SEARCH
    if VECTOR_SEARCH_AVAILABLE:
        # Only use FAISS search for better consistency - remove basic search
        tools = [faiss_search_documents, faiss_index_documents]
        description = f"Enhanced search agent with {VECTOR_TYPE} vector database for semantic search."
    else:
        # Fallback to basic search only if FAISS not available
        tools = [search_tool]
        description = "Enhanced search agent with improved contact and claims search."
    
    return LlmAgent(
        name="SearchAssistantAgent",
        model="gemini-2.0-flash-exp",
        instruction=search_assistant_prompt,
        description=description,
        tools=tools,
    )
