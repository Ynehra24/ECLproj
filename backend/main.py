import os
import json
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

# Load environment variables from .env placed in the backend folder
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:3000")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "SAGE Scenario Generator")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set. Create backend/.env with OPENROUTER_API_KEY=...")

app = FastAPI()

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Backend is running"}

class GenerateRequest(BaseModel):
    subjects: List[str]
    types: Optional[List[str]] = None

def build_prompt(subjects: List[str], types: Optional[List[str]]) -> str:
    subjects_str = ", ".join(subjects) if subjects else "General"
    types_str = ", ".join(types) if types else "MCQ"
    return (
        "You are a training scenario generator.\n"
        f"- Subjects: {subjects_str}\n"
        f"- Question types: {types_str}\n"
        "Task: Create a concise, engaging scenario for a training question.\n"
        "Return ONLY valid JSON with exactly these keys:\n"
        '{\n'
        '  "scenario": "3-6 sentences, no markdown",\n'
        '  "options": ["option A", "option B", "option C"]\n'
        "}\n"
        "No extra text, no backticks."
    )

def call_openrouter(subjects: List[str], types: Optional[List[str]]):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-Title": OPENROUTER_APP_NAME,
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": "You output only valid compact JSON per user instructions."},
            {"role": "user", "content": build_prompt(subjects, types)},
        ],
    }

    r = httpx.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    content = data["choices"][0]["message"]["content"]

    # Parse JSON content safely
    try:
        parsed = json.loads(content)
        scenario = str(parsed.get("scenario", "")).strip()
        options = parsed.get("options", [])
        if not scenario or not isinstance(options, list) or len(options) != 3:
            raise ValueError("Invalid JSON structure from model")
        return scenario, options
    except Exception:
        # Attempt to salvage JSON between braces
        try:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                parsed = json.loads(content[start : end + 1])
                scenario = str(parsed.get("scenario", "")).strip()
                options = parsed.get("options", [])
                if scenario and isinstance(options, list) and len(options) == 3:
                    return scenario, options
        except Exception:
            pass

        # Fallback
        subj = ", ".join(subjects) or "General"
        return (f"A short training scenario about {subj}.", ["Option A", "Option B", "Option C"])

@app.post("/generate")
def generate_scenario(request: GenerateRequest):
    if not request.subjects:
        raise HTTPException(status_code=400, detail="subjects must not be empty")

    try:
        scenario, options = call_openrouter(request.subjects, request.types)
        return {"scenario": scenario, "options": options}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OpenRouter error: {str(e)}")