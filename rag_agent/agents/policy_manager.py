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

"""Policy Manager Agent - Lists available insurance policies."""

from google.adk.agents import LlmAgent
from ..tools.policy_tools import list_files_tool


def create_policy_manager_agent(llm=None) -> LlmAgent:
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
