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
RAG Orchestrator Agent - Routes between policy management and search.
"""

import logging
from typing import AsyncGenerator
from typing_extensions import override

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGOrchestrator(BaseAgent):
    """
    Custom orchestrator for the Insurance Policy RAG workflow.

    Routes user requests to the appropriate agent:
    - Policy management queries → Policy Manager Agent
    - Search queries → Search Assistant Agent

    This agent checks the user's intent to intelligently route requests.
    """

    # Declare sub-agents as class attributes for Pydantic
    policy_manager: LlmAgent
    search_assistant: LlmAgent

    # Allow arbitrary types for Pydantic validation
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str,
        policy_manager: LlmAgent,
        search_assistant: LlmAgent,
    ):
        """
        Initialize the RAG Orchestrator.

        Args:
            name: The name of the orchestrator.
            policy_manager: Agent that handles policy management queries.
            search_assistant: Agent that handles search and answers questions.
        """
        # Define sub_agents list for framework
        sub_agents_list = [policy_manager, search_assistant]

        # Call super().__init__ with all required fields
        super().__init__(
            name=name,
            policy_manager=policy_manager,
            search_assistant=search_assistant,
            sub_agents=sub_agents_list,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Orchestration logic for routing requests.
        """
        logger.info(f"[{self.name}] Starting Insurance Policy RAG orchestration")

        # Get the user's latest message from session history
        user_text = ""
        if ctx.session.events and len(ctx.session.events) > 0:
            last_event = ctx.session.events[-1]
            if last_event.content and last_event.content.parts:
                for part in last_event.content.parts:
                    if part.text:
                        user_text = part.text.lower()
                        logger.info(f"[{self.name}] User text: {user_text[:100]}")
                        break  # Assuming one text part per user message

        # Routing Logic
        # If user asks about policies, route to policy manager.
        if any(
            keyword in user_text
            for keyword in ["list policies", "what policies", "show policies"]
        ):
            logger.info(
                f"[{self.name}] → Routing to Policy Manager (policy-related query)"
            )
            route_to_policy_manager = True
        else:
            logger.info(
                f"[{self.name}] → Routing to Search Assistant (search/question query)"
            )
            route_to_policy_manager = False

        # Execute the appropriate agent
        if route_to_policy_manager:
            logger.info(f"[{self.name}] Running Policy Manager Agent...")
            async for event in self.policy_manager.run_async(ctx):
                logger.info(f"[{self.name}] Event from PolicyManager: {event.author}")
                yield event
        else:
            logger.info(f"[{self.name}] Running Search Assistant Agent...")
            async for event in self.search_assistant.run_async(ctx):
                logger.info(
                    f"[{self.name}] Event from SearchAssistant: {event.author}"
                )
                yield event

        logger.info(f"[{self.name}] Orchestration complete")

    @override
    async def _run_live_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Orchestration logic for live/voice mode.

        In voice mode, we route directly to the SearchAssistant.
        Policy management is handled via text queries.
        """
        logger.info(f"[{self.name}] Starting LIVE orchestration (voice mode)")

        # Main voice interaction goes to SearchAssistant
        logger.info(f"[{self.name}] → Running Search Assistant in LIVE mode")
        async for event in self.search_assistant.run_live(ctx):
            logger.info(f"[{self.name}] Live event from SearchAssistant")
            yield event

        logger.info(f"[{self.name}] Live orchestration complete")

