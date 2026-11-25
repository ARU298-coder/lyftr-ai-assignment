from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, save_message, get_messages
from app.schemas import ChatRequest
from app.config import (
    LLM_API_KEYS,
    ALLOWED_ORIGINS,
    ENABLE_FAILURE_SIMULATION
)
from app.llm import call_llm


app = FastAPI(
    title="Lyftr AI Chatbot",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


init_db()


@app.get("/")
def root():
    return {
        "message": "Lyftr AI Backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "keys_configured": len(LLM_API_KEYS),
        "cache_enabled": True
    }


def parse_failure_header(header_value):
    failures = {}

    if not header_value:
        return failures

    allowed_statuses = {429, 500, 502, 503}

    for item in header_value.split(","):
        try:
            key_id, status = item.strip().split("=")
            status = int(status)

            if status in allowed_statuses:
                failures[key_id.strip()] = status

        except (ValueError, TypeError):
            continue

    return failures


@app.post("/chat")
def chat(
    request: ChatRequest,
    x_simulate_failure: str | None = Header(
        default=None,
        alias="X-Simulate-Failure"
    )
):
    # Load existing conversation BEFORE saving new message
    history = get_messages(request.session_id)

    messages = []

    system_prompt = (
        request.system_prompt
        or "You are a helpful AI assistant."
    )

    messages.append({
        "role": "system",
        "content": system_prompt
    })

    # Add previous conversation
    for item in history:
        messages.append({
            "role": item["role"],
            "content": item["content"]
        })

    # Add newest user message
    messages.append({
        "role": "user",
        "content": request.message
    })

    simulated_failures = {}

    if ENABLE_FAILURE_SIMULATION:
        simulated_failures = parse_failure_header(
            x_simulate_failure
        )

    try:
        result = call_llm(
            messages,
            simulated_failures
        )

    except RuntimeError:
        # IMPORTANT:
        # Failed request is NOT stored in SQLite
        raise HTTPException(
            status_code=503,
            detail="all providers unavailable"
        )

    metadata = {
        "resolution_source": result["resolution_source"],
        "model": result["model"],
        "latency_ms": result["latency_ms"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "key_id": result["key_id"],
        "fallback_attempts": result["fallback_attempts"]
    }

    # Only save after successful response
    save_message(
        request.session_id,
        "user",
        request.message
    )

    save_message(
        request.session_id,
        "assistant",
        result["reply"],
        metadata
    )

    return {
        "session_id": request.session_id,
        "reply": result["reply"],
        "metadata": metadata
    }


@app.get("/sessions/{session_id}/messages")
def session_messages(session_id: str):

    messages = get_messages(session_id)

    if not messages:
        raise HTTPException(
            status_code=404,
            detail="session not found"
        )

    return {
        "session_id": session_id,
        "messages": messages
    }