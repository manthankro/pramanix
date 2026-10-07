import json
import re
import time
from collections import defaultdict, deque

import anthropic
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .agent import run_agent
from .config import settings

app = FastAPI(title="Pramanix Project Agent")
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static", html=True), name="static")
app.add_middleware(CORSMiddleware, allow_origins=[settings.allowed_origin],
                   allow_methods=["POST", "GET"], allow_headers=["Content-Type"])

_hits = defaultdict(deque)


def allowed(ip):
    now, q = time.time(), _hits[ip]
    while q and q[0] < now - 60:
        q.popleft()
    if len(q) >= settings.rate_limit_per_min:
        return False
    q.append(now)
    return True


class ChatRequest(BaseModel):
    session_id: str = Field(pattern=r"^[A-Za-z0-9_-]{8,64}$")
    message: str = Field(min_length=1, max_length=2000)


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request):
    # Behind a reverse proxy, configure uvicorn --proxy-headers so client IPs are correct.
    if not allowed(request.client.host if request.client else "unknown"):
        raise HTTPException(429, "Too many requests. Please wait a minute.")

    async def stream():
        try:
            async for ev in run_agent(req.session_id, req.message):
                yield f"data: {json.dumps(ev)}\n\n"
        except anthropic.APIError:
            yield f"data: {json.dumps({'type': 'error', 'text': 'The AI service is unavailable. Try again shortly.'})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
