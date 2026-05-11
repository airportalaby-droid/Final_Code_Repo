FIX_PROMPT_TEMPLATE = """Fix this security vulnerability and respond with ONLY a JSON object.

Vulnerability: {vulnerability_type}
Code: {code_snippet}

Return exactly this JSON format (replace all placeholder values with your actual analysis):
{{"rationale": "<explain why this specific code is dangerous and what the risk is>", "fixed_code": "<the secure version of the code>", "confidence": <integer 0-100 reflecting how confident you are in this fix; use higher values like 90-100 for well-known exploits with clear fixes, 60-80 for moderate confidence, and below 60 when the fix is uncertain>}}

IMPORTANT: The confidence value must be an integer you calculate based on the severity and clarity of the fix. Do NOT use 85 as a default."""
