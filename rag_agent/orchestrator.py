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
from .utils.routing import extract_user_text, determine_route

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGOrchestrator(BaseAgent):
    """
    Custom orchestrator for the Insurance Policy RAG workflow.

    Routes user requests to the appropriate agent:
    - Policy management queries → Policy Manager Agent
    - Search queries → Search Assistant Agent
    - Voice queries → Voice Assistant Agent

    This agent checks the user's intent to intelligently route requests.
    """

    # Declare sub-agents as class attributes for Pydantic
    policy_manager: LlmAgent
    search_assistant: LlmAgent
    voice_assistant: LlmAgent

    # Allow arbitrary types for Pydantic validation
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str,
        policy_manager: LlmAgent,
        search_assistant: LlmAgent,
        voice_assistant: LlmAgent,
    ):
        """
        Initialize the RAG Orchestrator.

        Args:
            name: The name of the orchestrator.
            policy_manager: Agent that handles policy management queries.
            search_assistant: Agent that handles search and answers questions.
            voice_assistant: Agent that handles voice interactions.
        """
        # Define sub_agents list for framework
        sub_agents_list = [policy_manager, search_assistant, voice_assistant]

        # Call super().__init__ with all required fields
        super().__init__(
            name=name,
            policy_manager=policy_manager,
            search_assistant=search_assistant,
            voice_assistant=voice_assistant,
            sub_agents=sub_agents_list,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Orchestration logic for routing text requests.
        """
        logger.info(f"[{self.name}] Starting Insurance Policy RAG orchestration")

        # Extract user text and determine routing
        user_text = extract_user_text(ctx)
        logger.info(f"[{self.name}] User text: {user_text[:100]}")

        # Check if this is a voice-related request or audio input
        voice_keywords = ["audio", "voice", "speak", "listen", "microphone", "speech", "say"]
        is_voice_request = any(keyword in user_text.lower() for keyword in voice_keywords)
        
        # Also check if there are audio attachments or voice input context
        has_audio_context = hasattr(ctx, 'attachments') and any(
            getattr(att, 'content_type', '').startswith('audio/') 
            for att in getattr(ctx, 'attachments', [])
        )
        
        if is_voice_request or has_audio_context:
            logger.info(f"[{self.name}] Running Voice Assistant Agent (bridge mode)...")
            async for event in self.voice_assistant.run_async(ctx):
                logger.info(f"[{self.name}] Event from VoiceAssistant: {event.author}")
                yield event
        else:
            route = determine_route(user_text)
            # Execute the appropriate agent
            if route == "policy_manager":
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

        In live mode, route to voice assistant for speech-to-text bridge functionality.
        """
        logger.info(f"[{self.name}] Starting LIVE orchestration (voice mode)")

        # In live mode, use voice assistant as bridge to search functionality
        logger.info(f"[{self.name}] → Running Voice Assistant in LIVE mode (bridge to search)")
        async for event in self.voice_assistant.run_live(ctx):
            logger.info(f"[{self.name}] Live event from VoiceAssistant")
            yield event

        logger.info(f"[{self.name}] Live orchestration complete")

