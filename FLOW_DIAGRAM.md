# System Flow Diagram

## User Request Flow (Text & Voice)

```
┌─────────────────────┐
│   User Input        │
│  (Text or Voice)    │
└──────────┬──────────┘
           │
           v
┌─────────────────────────────────────────┐
│         RAG Orchestrator                │
│                                         │
│  1. Extract text from context          │
│  2. Determine route via keywords       │
└──────────┬──────────────────────────────┘
           │
           v
    ┌──────┴──────┐
    │   Routing   │
    │   Logic     │
    └──────┬──────┘
           │
           v
    Keywords found?
           │
     ┌─────┴─────┐
     │           │
     v           v
  Yes           No
     │           │
     v           v
┌────────────┐  ┌─────────────────┐
│  Policy    │  │  Search         │
│  Manager   │  │  Assistant      │
│  Agent     │  │  Agent          │
└─────┬──────┘  └────────┬────────┘
      │                  │
      v                  v
┌────────────┐  ┌─────────────────┐
│ List Files │  │ Search          │
│ Tool       │  │ Documents Tool  │
└─────┬──────┘  └────────┬────────┘
      │                  │
      v                  v
┌────────────┐  ┌─────────────────┐
│ Return     │  │ Return          │
│ Policy     │  │ Answer from     │
│ List       │  │ Indexed Docs    │
└─────┬──────┘  └────────┬────────┘
      │                  │
      └────────┬─────────┘
               v
     ┌──────────────────┐
     │  Response to     │
     │  User            │
     └──────────────────┘
```

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Orchestrator                         │
│                                                             │
│  Responsibilities:                                          │
│  - Route text requests (_run_async_impl)                   │
│  - Route voice requests (_run_live_impl)                   │
│  - Use centralized routing logic                           │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        v                v                v
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Policy     │  │   Search     │  │   Utils/     │
│   Manager    │  │   Assistant  │  │   Routing    │
│              │  │              │  │              │
│ - Lists      │  │ - Answers    │  │ - Extract    │
│   policies   │  │   questions  │  │   text       │
│              │  │ - Searches   │  │ - Determine  │
│              │  │   docs       │  │   route      │
└──────┬───────┘  └──────┬───────┘  └──────────────┘
       │                 │
       v                 v
┌──────────────┐  ┌──────────────┐
│ Policy Tools │  │ Search Tools │
│              │  │              │
│ - list_files │  │ - search_    │
│   _tool      │  │   documents  │
│              │  │              │
└──────────────┘  └──────────────┘
```

## Routing Logic Details

```python
def determine_route(user_text: str) -> str:
    """
    Policy Manager Keywords:
    - "list policies"
    - "what policies"
    - "show policies"
    - "available policies"
    - "which policies"
    - "policy list"
    
    Returns:
    - "policy_manager" if keywords found
    - "search_assistant" otherwise (default)
    """
```

## Voice Processing Flow

```
Voice Input
    │
    v
[Transcribed to Text]
    │
    v
Extract User Text
    │
    v
Determine Route (same as text)
    │
    v
Execute Agent in LIVE mode
    │
    v
[Response converted to Voice]
    │
    v
Voice Output
```

## Key Improvements

1. **Unified Routing**: Both text and voice use `determine_route()`
2. **Extensible**: Easy to add new agents and keywords
3. **Maintainable**: Clear separation of concerns
4. **Consistent**: Same behavior for text and voice
