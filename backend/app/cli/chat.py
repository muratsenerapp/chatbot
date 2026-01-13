"""Minimal CLI entrypoint to query the local LLM via the backend service layer and stream output to stdout."""

import os
import sys
import asyncio
from app.services.llm import LLMClient


async def main() -> None:
    """Run a one-off chat prompt from the command line.

    Streams the model's response to stdout for quick manual checks.
    """
    prompt = " ".join(sys.argv[1:]) or "Briefly introduce yourself."
    client = LLMClient(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct"),
    )
    # stream to stdout
    async for t in client.astream_chat([prompt]):
        print(t, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
