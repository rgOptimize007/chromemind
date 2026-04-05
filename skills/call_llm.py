"""
Skill: call_llm
Role: Generic Gemini SDK wrapper with retry and rate limiting.
Input: prompt (str), model name, temperature, max_tokens
Output: str (LLM response text) | raises SkillError
Used by: EnrichmentAgent
"""

import os
import time
from chromemind.errors import SkillError

# Track last call time for rate limiting
_last_call_time = 0.0


def call_llm(prompt: str, model: str = "gemini-2.0-flash",
             temperature: float = 0.2, max_tokens: int = 300,
             max_retries: int = 1) -> str:
    """Calls Gemini API and returns the response text."""
    global _last_call_time

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise SkillError("GEMINI_API_KEY not set or still placeholder in .env")

    from google import genai

    client = genai.Client(api_key=api_key)

    # Rate limit: min 6 seconds between calls (10 calls/min)
    elapsed = time.time() - _last_call_time
    if elapsed < 6.0:
        time.sleep(6.0 - elapsed)

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            _last_call_time = time.time()
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )

            if response.text:
                return response.text.strip()
            else:
                raise SkillError("Gemini returned empty response")

        except SkillError:
            raise
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # exponential backoff
                continue

    raise SkillError(f"LLM call failed after {max_retries + 1} attempts: {last_error}")
