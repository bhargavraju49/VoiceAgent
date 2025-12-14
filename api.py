import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

import run as run_module  # your run.py where main() returns orchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ---- Absolute UI path (fixes "micBtn not found") ----
BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"

# ---- ADK runner globals ----
runner: Optional[Runner] = None
session_service: Optional[InMemorySessionService] = None
APP_NAME = "voiceagent-ui"
USER_ID = "local-user"
SESSION_ID: Optional[str] = None


class ChatRequest(BaseModel):
    text: str


@app.on_event("startup")
async def startup():
    global runner, session_service, SESSION_ID

    logger.info("Starting ADK agent + Runner...")
    orchestrator = await run_module.main()  # run.py main returns orchestrator

    session_service = InMemorySessionService()
    runner = Runner(agent=orchestrator, app_name=APP_NAME, session_service=session_service)

    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    SESSION_ID = session.id

    logger.info(f"✅ Runner ready. session_id={SESSION_ID}")


# ---- UI routes ----
@app.get("/")
def home():
    return FileResponse(UI_DIR / "index.html")

@app.get("/style.css")
def css():
    return FileResponse(UI_DIR / "style.css")

@app.get("/app.js")
def js():
    return FileResponse(UI_DIR / "app.js")

@app.get("/favicon.ico")
def favicon():
    return JSONResponse({}, status_code=204)


# ---- Chat endpoint ----
@app.post("/chat")
async def chat(req: ChatRequest):
    if runner is None or SESSION_ID is None:
        return JSONResponse(status_code=503, content={"answer": "Backend not ready yet. Try again."})


    user_text = (req.text or "").strip()
    if not user_text:
        return {"answer": "Please type a question."}


    # Prepend system instruction for concise answers and always include coverage numbers
    system_instruction = "Answer in 1-2 sentences. Be brief and to the point. Always include the coverage amount or limit in your answer if available."
    content = [
        types.Content(role="system", parts=[types.Part(text=system_instruction)]),
        types.Content(role="user", parts=[types.Part(text=user_text)])
    ]

    final_text = ""

    try:
        # If runner.run_async supports 'messages', use it; else fallback to 'new_message'
        run_async_args = dict(user_id=USER_ID, session_id=SESSION_ID)
        # Try 'messages' argument (for list of messages)
        try:
            async for event in runner.run_async(messages=content, **run_async_args):
                if getattr(event, "content", None) and getattr(event.content, "parts", None):
                    text_parts = [p.text for p in event.content.parts if getattr(p, "text", None)]
                    if text_parts:
                        final_text = "\n".join(text_parts)
                if hasattr(event, "is_final_response") and event.is_final_response():
                    break
        except TypeError:
            # Fallback for older ADK: send only user message
            async for event in runner.run_async(new_message=content[-1], **run_async_args):
                if getattr(event, "content", None) and getattr(event.content, "parts", None):
                    text_parts = [p.text for p in event.content.parts if getattr(p, "text", None)]
                    if text_parts:
                        final_text = "\n".join(text_parts)
                if hasattr(event, "is_final_response") and event.is_final_response():
                    break

        return {"answer": final_text.strip() or "No answer produced."}

    except Exception as e:
        logger.exception("Chat failed")
        return JSONResponse(status_code=500, content={"answer": f"Server error: {str(e)}"})
