# Project Structure Documentation

## Overview
This project implements a multi-agent RAG (Retrieval-Augmented Generation) system for insurance policy question-answering with voice and text support.

## New Organized Structure
```
rag_agent/
├── __init__.py                 # Main package initialization
├── agent.py                    # Root agent creation and exports
├── orchestrator.py             # Main orchestrator that routes requests
│
├── agents/                     # Agent definitions
│   ├── __init__.py
│   ├── policy_manager.py      # Lists available policies
│   ├── search_assistant.py    # Answers questions about policies
│   └── file_manager.py        # Handles file processing/indexing
│
├── tools/                      # Tool definitions
│   ├── __init__.py
│   ├── policy_tools.py        # Tools for listing & processing policies
│   └── search_tools.py        # Tools for searching documents
│
└── utils/                      # Utility functions
    ├── __init__.py
    └── routing.py             # Request routing logic (text & voice)
```

## Key Components

### 1. **Orchestrator** (`orchestrator.py`)
- Routes user requests to the appropriate agent
- Handles both **text** (`_run_async_impl`) and **voice** (`_run_live_impl`) modes
- Uses keyword-based routing for both text and voice

### 2. **Agents** (`agents/`)
- **Policy Manager**: Lists available insurance policies
- **Search Assistant**: Answers questions using indexed policy content
- **File Manager**: Processes and indexes policy documents

### 3. **Tools** (`tools/`)
- **Policy Tools**: List policies, process files
- **Search Tools**: Search through indexed documents

### 4. **Utils** (`utils/`)
- **Routing**: Extract user text and determine which agent to route to

## Voice & Text Routing

Both voice and text queries are now routed using the **same keyword-based logic**:

### Keywords for Policy Manager:
- "list policies"
- "what policies"
- "show policies"
- "available policies"
- "which policies"
- "policy list"

### Default (Search Assistant):
- All other queries (questions about policy content)

## How It Works

1. **User Query** → Orchestrator receives request
2. **Extract Text** → Extract user's input (from text or voice)
3. **Determine Route** → Match keywords to decide agent
4. **Execute Agent** → Run appropriate agent (policy_manager or search_assistant)
5. **Return Response** → Stream events back to user

## Migration Notes

### Old Structure → New Structure
- `file_upload_handler.py` → `tools/policy_tools.py`
- `file_search_tool.py` → `tools/search_tools.py`
- Agent functions in `agent.py` → `agents/policy_manager.py`, `agents/search_assistant.py`, `agents/file_manager.py`
- Routing logic → `utils/routing.py`

### What Changed
1. ✅ Voice routing now uses keywords (was hardcoded to search_assistant)
2. ✅ Organized files into logical directories
3. ✅ Extracted reusable routing logic
4. ✅ Cleaner separation of concerns

## Usage

The `root_agent` in `agent.py` is the entry point for the ADK system:

```python
from rag_agent.agent import root_agent
# ADK automatically discovers and uses root_agent
```
