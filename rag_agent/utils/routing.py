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

"""Routing utilities for the RAG Orchestrator."""

import logging
from typing import Optional
from google.adk.agents.invocation_context import InvocationContext

logger = logging.getLogger(__name__)


def extract_user_text(ctx: InvocationContext) -> str:
    """
    Extract the user's text from the invocation context.

    Args:
        ctx: The invocation context.

    Returns:
        The user's text in lowercase, or an empty string if not found.
    """
    user_text = ""
    if ctx.session.events and len(ctx.session.events) > 0:
        last_event = ctx.session.events[-1]
        if last_event.content and last_event.content.parts:
            for part in last_event.content.parts:
                if part.text:
                    user_text = part.text.lower()
                    break
    return user_text


def determine_route(user_text: str) -> str:
    """
    Determine which agent should handle the request based on keywords.

    Args:
        user_text: The user's input text (lowercase).

    Returns:
        The agent name to route to: "policy_manager" or "search_assistant".
    """
    # Keywords for policy management
    policy_keywords = [
        "list policies",
        "what policies",
        "show policies",
        "available policies",
        "which policies",
        "policy list",
    ]

    # Check if user is asking about policies
    if any(keyword in user_text for keyword in policy_keywords):
        logger.info("→ Routing to Policy Manager (policy-related query)")
        return "policy_manager"
    else:
        logger.info("→ Routing to Search Assistant (search/question query)")
        return "search_assistant"
