"""Settings from .env, and the one place that decides which AI model the whole team uses."""
import contextvars
import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as CallTimeout
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
CALL_TIMEOUT = int(os.getenv("LLM_CALL_TIMEOUT", "120"))  # Gemini's client has no timeout; a stuck call froze runs
_calls = ThreadPoolExecutor(max_workers=4, thread_name_prefix="llm")
_BUSY = ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "overloaded", "high demand", "rate limit")


def with_fallback(llms):
    """First model answers normally; when it is busy or out of free quota, the next model takes the same call."""
    first = llms[0]
    calls = [l.call for l in llms]

    def call(*args, **kwargs):
        for i, c in enumerate(calls):
            try:
                # shortcut: a call that hangs keeps its thread busy in the background until the provider gives up;
                # fine for one run at a time, revisit if runs ever go parallel.
                job = _calls.submit(contextvars.copy_context().run, c, *args, **kwargs)
                try:
                    return job.result(timeout=CALL_TIMEOUT)
                except CallTimeout:
                    raise RuntimeError(f"503 no answer from {llms[i].model} in {CALL_TIMEOUT}s (overloaded)") from None
            except Exception as e:
                if not any(s.lower() in str(e).lower() for s in _BUSY):
                    raise
                if i == len(calls) - 1:
                    if "per day" in str(e).lower() or "perday" in str(e).lower():
                        raise RuntimeError("Gemini's free daily limit is used up on every model (it resets in about a day). "
                                           "Wait, or set LLM_PROVIDER=groq or ollama in .env and restart start.bat.") from None
                    raise
                on_switch(f"{llms[i].model} is busy, switching to {llms[i + 1].model}")

    object.__setattr__(first, "call", call)  # LLM is a pydantic model; set the wrapper on this one instance
    return first


def _cap_provider_wait():
    """CrewAI sleeps as long as the provider says ("retry in 12h" on a used-up daily quota), which freezes a run.
    Cap it at 20s so we move on to the next model instead."""
    from crewai.llms import retry
    if getattr(retry, "_weblume_capped", False):
        return
    retry._weblume_capped = True
    original = retry._retry_after_seconds
    retry._retry_after_seconds = lambda e: (lambda s: None if s is None else min(s, 20.0))(original(e))


def get_llm():
    """Build the LLM for every agent. Change LLM_PROVIDER in .env to switch."""
    from crewai import LLM

    _cap_provider_wait()
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
    if PROVIDER == "bytez":
        key = os.getenv("BYTEZ_API_KEY", "").strip()
        if not key or not model:
            raise RuntimeError("Bytez needs BYTEZ_API_KEY and LLM_MODEL (a model id from bytez.com) in .env.")
        # Bytez speaks the OpenAI API at its own address
        return LLM(model=f"openai/{model}", base_url="https://api.bytez.com/models/v2/openai/v1", api_key=key, temperature=0.7)
    if PROVIDER == "ollama":
        url = os.getenv("OLLAMA_URL", "http://localhost:11434").strip()
        return LLM(model=f"ollama/{model}", base_url=url, api_key="ollama", temperature=0.7)
    raise RuntimeError(f"LLM_PROVIDER must be gemini, groq, bytez or ollama (got '{PROVIDER}').")
