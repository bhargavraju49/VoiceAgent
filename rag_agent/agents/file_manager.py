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

"""File Manager Agent - Handles file processing and indexing."""

from google.adk.agents import LlmAgent
from ..tools.policy_tools import file_processing_tool


def create_file_manager_agent(llm=None) -> LlmAgent:
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
