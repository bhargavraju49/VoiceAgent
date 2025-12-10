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

"""RAG Agent definitions for the Insurance Policy Q&A agent."""

from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from .file_search_tool import search_tool
from .file_upload_handler import list_files_tool, file_processing_tool
from .orchestrator import RAGOrchestrator


def create_policy_manager_agent(llm) -> LlmAgent:
    """
    Creates the Policy Manager agent.

    This agent is responsible for listing the available insurance policies.
    """
    policy_manager_prompt = """
    You are a Policy Manager Assistant. Your job is to list the available insurance policies.

    **Your Tool:**
    - `list_files`: Use this tool to get a list of all indexed policies.

    **Workflow:**
    1. When the user asks to see the policies, call the `list_files` tool.
    2. Present the list of policies to the user.
    """
    return LlmAgent(
        name="PolicyManagerAgent",
        model="gemini-2.0-flash-exp",
        instruction=policy_manager_prompt,
        description="Manages listing of insurance policies.",
        tools=[list_files_tool],
    )


def create_search_assistant_agent(llm) -> LlmAgent:
    """
    Creates the Search Assistant agent.

    This agent is responsible for answering questions based on the content
    of the indexed insurance policies.
    """
    search_assistant_prompt = """
    You are a Search Assistant for insurance policies. Your sole purpose is to answer
    questions using only the content from the indexed policy documents.

    **Your Tool:**
    - `search_documents`: Use this to find answers in the indexed policies.

    **How to Respond:**
    1.  **Always use the `search_documents` tool** to answer user questions.
    2.  Base your answers strictly on the information returned by the tool.
    3.  If the answer is found, summarize it clearly. Always cite the source policy.
    4.  If the answer cannot be found, state: "I could not find information about that
        in the available insurance policies."
    5.  Do not use general knowledge.
    """
    return LlmAgent(
        name="SearchAssistantAgent",
        model="gemini-2.0-flash-exp",
        instruction=search_assistant_prompt,
        description="Answers questions about insurance policies.",
        tools=[search_tool],
    )


def create_file_manager_agent(llm) -> LlmAgent:
    """
    Creates the File Manager agent for startup indexing.

    This agent is not directly used by the orchestrator but its tool is
    used in the startup script for indexing.
    """
    return LlmAgent(
        name="FileManagerAgent",
        model="gemini-2.0-flash-exp",
        tools=[file_processing_tool],
        description="A helper agent for file processing.",
    )


# Create the root agent that ADK will discover
def create_root_agent():
    """Create the main orchestrator agent for ADK discovery."""
    
    policy_manager = create_policy_manager_agent(None)
    search_assistant = create_search_assistant_agent(None)
    
    return RAGOrchestrator(
        name="InsurancePolicyRAGOrchestrator",
        policy_manager=policy_manager,
        search_assistant=search_assistant,
    )


# This is what ADK looks for
root_agent = create_root_agent()
