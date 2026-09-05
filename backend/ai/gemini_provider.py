"""
Payment Burst Sentinel — Gemini Provider
==========================================
Implements InvestigationAIProvider using the google-genai SDK
with native Pydantic structured output and multi-model fallback.
"""

import asyncio
import logging
import os
from typing import Optional, List

from google import genai
from google.genai import types as genai_types

from .provider import InvestigationAIProvider
from .schemas import InvestigationEvidence, InvestigationBrief, AIBriefResponse
from .prompt_builder import build_system_instruction, build_prompt
from .guardrails import validate_brief

logger = logging.getLogger(__name__)

# Verified Flash models from Google AI Studio in priority cascade:
# 1. gemini-3.8-flash: Latest cutting-edge Flash model (high performance & reasoning)
# 2. gemini-3.7-flash: Advanced reasoning Flash model
# 3. gemini-3.5-flash: Active AI Studio flagship model
# 4. gemini-3.5-flash-lite: High throughput fallback (500 requests/day quota)
# 5. gemini-3.1-flash-lite: Alternative high-volume fallback (500 requests/day quota)
# 6. gemini-2.5-flash: Standard Flash fallback
# 7. gemini-2.5-flash-lite: Lightweight standard Flash model
DEFAULT_MODELS: List[str] = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]
DEFAULT_MODEL = DEFAULT_MODELS[0]
REQUEST_TIMEOUT = 45  # seconds


class GeminiProvider(InvestigationAIProvider):
    """Gemini-powered investigation AI provider with structured output and fallback cascade."""

    def __init__(self, models: Optional[List[str]] = None):
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        self._client = genai.Client(api_key=api_key)

        if models:
            self._models = list(models)
        else:
            env_models = os.environ.get("GEMINI_MODEL", "")
            if env_models:
                self._models = [m.strip() for m in env_models.split(",") if m.strip()]
            else:
                self._models = list(DEFAULT_MODELS)

        self._active_model = self._models[0]

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._active_model

    @property
    def models(self) -> List[str]:
        return list(self._models)

    async def generate_brief(
        self, evidence: InvestigationEvidence
    ) -> AIBriefResponse:
        """Generate investigation brief using Gemini with multi-model fallback."""
        system_instruction = build_system_instruction()
        user_prompt = build_prompt(evidence)
        valid_ids = {item.evidence_id for item in evidence.evidence_items}

        errors = []

        # Iterate through models in priority cascade order
        for model in self._models:
            for attempt in range(2):
                try:
                    logger.info(f"Attempting brief generation with {model} (attempt {attempt + 1})")
                    brief = await self._call_gemini(
                        model, system_instruction, user_prompt
                    )

                    if brief is None:
                        if attempt == 0:
                            logger.warning(f"Model {model} returned empty response, retrying...")
                            continue
                        errors.append(f"{model}: empty response")
                        break

                    # Validate through 7 guardrails
                    validation_error = validate_brief(brief, valid_ids)
                    if validation_error:
                        if attempt == 0:
                            logger.warning(
                                f"Guardrail validation failed on {model}: {validation_error}. Retrying..."
                            )
                            continue
                        logger.error(f"Guardrail validation failed after retry on {model}: {validation_error}")
                        errors.append(f"{model}: guardrail failed ({validation_error})")
                        break

                    # Success!
                    self._active_model = model
                    return AIBriefResponse.available(
                        brief=brief,
                        provider=self.provider_name,
                        model=model,
                    )

                except asyncio.TimeoutError:
                    logger.warning(f"Model {model} timed out after {REQUEST_TIMEOUT}s")
                    errors.append(f"{model}: request timed out")
                    break  # Fall back to next model on timeout

                except Exception as e:
                    err_str = str(e)
                    logger.warning(f"Model {model} error: {err_str}")
                    if attempt == 0 and not any(k in err_str.lower() for k in ("429", "503", "quota", "unavailable")):
                        continue
                    errors.append(f"{model}: {err_str}")
                    break  # Fall back to next model on error or quota limit

        # If all candidate models in cascade failed:
        logger.error(f"All Gemini models in cascade failed: {'; '.join(errors)}")
        return AIBriefResponse.unavailable(
            "AI service encountered an error across candidate models. "
            "The deterministic evidence remains available."
        )

    async def _call_gemini(
        self, model: str, system_instruction: str, user_prompt: str
    ) -> Optional[InvestigationBrief]:
        """Execute the Gemini API call with structured output for a specific model."""
        try:
            config = genai_types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
                max_output_tokens=4096,
                response_mime_type="application/json",
                response_schema=InvestigationBrief,
            )

            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._client.models.generate_content(
                        model=model,
                        contents=user_prompt,
                        config=config,
                    ),
                ),
                timeout=REQUEST_TIMEOUT,
            )

            if not response or not response.text:
                return None

            import json
            brief_data = json.loads(response.text)
            return InvestigationBrief(**brief_data)

        except asyncio.TimeoutError:
            raise
        except Exception as e:
            logger.error(f"Gemini API call failed for model {model}: {e}")
            raise
