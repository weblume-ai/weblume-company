"""Settings from .env, and the one place that decides which AI model the whole team uses."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OUTPUT_DIR = ROOT / "output"
RUNS_DIR = OUTPUT_DIR / "runs"
CONTACTED_FILE = ROOT / "contacted.json"

PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
WEBSITE = os.getenv("WEBLUME_WEBSITE", "https://weblume-sa.github.io/").strip()
CURRENCY = os.getenv("PRICE_CURRENCY", "EGP").strip()
MAX_RPM = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "8"))  # Gemini free tier allows about 10 per minute

DEFAULT_MODELS = {
    "gemini": "gemini-3.5-flash",  # 2.5-flash is closed to new accounts; 3.8 is often overloaded (Nov 2026)
    "groq": "llama-3.3-70b-versatile",
    "ollama": "qwen2.5:7b",
}


def model_name() -> str:
    return os.getenv("LLM_MODEL", "").strip() or DEFAULT_MODELS.get(PROVIDER, "")


on_switch = print  # company.py points this at the run log while a run is going
_BUSY = ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "overloaded", "high demand", "rate limit")


def with_fallback(llms):
    """First model answers normally; when it is busy or out of free quota, the next model takes the same call."""
    first = llms[0]
    calls = [l.call for l in llms]

    def call(*args, **kwargs):
        for i, c in enumerate(calls):
            try:
                return c(*args, **kwargs)
            except Exception as e:
                if i == len(calls) - 1 or not any(s.lower() in str(e).lower() for s in _BUSY):
                    raise
                on_switch(f"{llms[i].model} is busy, switching to {llms[i + 1].model}")

    object.__setattr__(first, "call", call)  # LLM is a pydantic model; set the wrapper on this one instance
    return first


def get_llm():
    """Build the LLM for every agent. Change LLM_PROVIDER in .env to switch."""
    from crewai import LLM

    model = model_name()
    if PROVIDER == "gemini":
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("GEMINI_API_KEY is empty in .env. Get a free key at https://aistudio.google.com/apikey")
        backups = [m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.8-flash,gemini-3.1-flash-lite")
                   .split(",") if m.strip() and m.strip() != model]
        llms = [LLM(model=f"gemini/{m}", api_key=key, temperature=0.7) for m in [model, *backups]]
        return with_fallback(llms)
    if PROVIDER == "groq":
        key = os.getenv("GROQ_API_KEY", "").strip()
        if not key:
            raise RuntimeError("GROQ_API_KEY is empty in .env. Get a free key at https://console.groq.com/keys")
        # Groq speaks the OpenAI API, so CrewAI's built-in OpenAI client works with Groq's address
        return LLM(model=f"openai/{model}", base_url="https://api.groq.com/openai/v1", api_key=key, temperature=0.7)
    if PROVIDER == "ollama":
        url = os.getenv("OLLAMA_URL", "http://localhost:11434").strip()
        return LLM(model=f"ollama/{model}", base_url=url, api_key="ollama", temperature=0.7)
    raise RuntimeError(f"LLM_PROVIDER must be gemini, groq or ollama (got '{PROVIDER}').")
