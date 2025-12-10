# Local Testing Guide

## Prerequisites Check

1. ✅ Python virtual environment exists: `venv/`
2. ✅ Environment file exists: `.env`
3. ✅ Requirements file exists: `requirements.txt`

## Step-by-Step Testing

### 1. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 2. Install/Update Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Environment Variables

Make sure your `.env` file has:
```
GOOGLE_API_KEY=your_api_key_here
```

### 4. Test the Agent Setup

Run the setup script to index policies:
```bash
python run.py
```

This will:
- Index any new policy files in `data/raw_policies/`
- Create indexed files in `data/indexed_policies/`
- Prepare the agent for queries

### 5. Start the ADK Web Interface

```bash
adk web
```

Then open: http://localhost:8000

### 6. Alternative: Test with ADK CLI

```bash
# Test a text query
adk run --agent-path rag_agent.agent:root_agent --query "list policies"

# Test a search query
adk run --agent-path rag_agent.agent:root_agent --query "what is covered in the policy?"
```

## Quick Test Commands

### Test Text Routing
```bash
# Should route to Policy Manager
adk run --agent-path rag_agent.agent:root_agent --query "show me available policies"

# Should route to Search Assistant
adk run --agent-path rag_agent.agent:root_agent --query "what are the terms and conditions?"
```

### Test Voice Mode (if supported)
```bash
adk run --agent-path rag_agent.agent:root_agent --live
```

## Troubleshooting

### If "adk" command not found:
```bash
pip install google-adk
```

### If import errors occur:
```bash
pip install --upgrade google-adk google-generativeai
```

### If no policies are indexed:
1. Add PDF files to `data/raw_policies/`
2. Run `python run.py` again

### Check indexed policies:
```bash
ls -la data/indexed_policies/
cat file_store_config.json
```

## Expected Output

### For "list policies" query:
```
Routing to Policy Manager
Returns: List of indexed policy files
```

### For content questions:
```
Routing to Search Assistant
Returns: Answer from policy documents with sources
```

## Testing Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] API key configured in .env
- [ ] Policies indexed (run.py executed)
- [ ] ADK web interface starts
- [ ] Text queries work
- [ ] Voice routing works (if using live mode)
- [ ] Both Policy Manager and Search Assistant respond correctly
