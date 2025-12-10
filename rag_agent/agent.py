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

from .agents import (
    create_policy_manager_agent,
    create_search_assistant_agent,
    create_file_manager_agent,
)
from .orchestrator import RAGOrchestrator


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
