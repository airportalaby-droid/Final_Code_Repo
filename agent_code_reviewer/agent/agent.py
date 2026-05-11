from typing import Union, Dict
import ollama
import json
import re
from agent.prompts import FIX_PROMPT_TEMPLATE


def generate_fix(vulnerability_type: str, code_snippet: str, model_name: str = "qwen3") -> Union[Dict, str]:
    """Generate a secure fix for the vulnerable code."""

    prompt = FIX_PROMPT_TEMPLATE.format(
        vulnerability_type=vulnerability_type,
        code_snippet=code_snippet,
    )

    try:
        messages = [
            {"role": "system", "content": "You are a code security expert. Respond with only valid JSON, no markdown, no explanation outside JSON."},
            {"role": "user", "content": prompt},
        ]

        response = ollama.chat(
            model=model_name,
            messages=messages,
            options={
                "temperature": 0.3,
                "num_predict": 512,
                "num_ctx": 2048,
            },
        )

        content = response["message"]["content"]

        # Strip qwen3 thinking tags if present
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

        # Remove markdown code fences if present
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = content.strip()

        # Try to parse JSON from the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                raw_confidence = result.get("confidence", 75)
                try:
                    confidence = max(0, min(100, int(raw_confidence)))
                except (ValueError, TypeError):
                    confidence = 75
                return {
                    "rationale": result.get("rationale", "Security improvement recommended"),
                    "fixed_code": result.get("fixed_code", code_snippet),
                    "confidence": confidence,
                }
            except json.JSONDecodeError:
                pass

        # Fallback: return the raw text as a structured response
        if content:
            return {
                "rationale": content[:500],
                "fixed_code": code_snippet,
                "confidence": 50,
            }

        return {
            "rationale": "The model did not return a valid response. Manual review recommended.",
            "fixed_code": code_snippet,
            "confidence": 0,
        }

    except Exception as e:
        return {
            "error": f"Failed to generate fix: {str(e)}",
            "rationale": "Manual review recommended",
            "fixed_code": code_snippet,
            "confidence": 0,
        }
