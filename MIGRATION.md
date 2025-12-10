# Migration Guide

## Files to Keep vs Deprecate

### ✅ Keep These (New Organized Structure)
```
rag_agent/
├── agent.py                    # ✅ Updated - use this
├── orchestrator.py             # ✅ Updated - use this
├── agents/                     # ✅ New organized agents
│   ├── policy_manager.py
│   ├── search_assistant.py
│   └── file_manager.py
├── tools/                      # ✅ New organized tools
│   ├── policy_tools.py
│   └── search_tools.py
└── utils/                      # ✅ New utilities
    └── routing.py
```

### ⚠️ Deprecated (Can be safely deleted)
```
rag_agent/
├── file_upload_handler.py      # ⚠️ Replaced by tools/policy_tools.py
└── file_search_tool.py         # ⚠️ Replaced by tools/search_tools.py
```

## How to Clean Up (Optional)

You can safely delete the old files:

```bash
cd /Users/bhargavasivaramarajupenumetcha/hackathon/rag_agent
rm file_upload_handler.py
rm file_search_tool.py
```

**Note**: The new organized structure is already in place and working. The old files are not being used anymore.

## Import Changes

### Before
```python
from rag_agent.file_upload_handler import list_files_tool
from rag_agent.file_search_tool import search_tool
```

### After
```python
from rag_agent.tools import list_files_tool, search_tool
# or
from rag_agent.tools.policy_tools import list_files_tool
from rag_agent.tools.search_tools import search_tool
```

## No Breaking Changes

The `agent.py` file still exports all the same functions:
```python
from rag_agent.agent import (
    create_policy_manager_agent,
    create_search_assistant_agent,
    create_file_manager_agent,
    root_agent
)
```

So existing code using these imports will continue to work! ✅

## Testing the Changes

Run your agent as usual:
```bash
python run.py
```

Everything should work exactly the same, but with:
- Better organization
- Voice routing with keywords (new feature!)
- Cleaner code structure
