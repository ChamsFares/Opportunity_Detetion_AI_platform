import json
import os
import re

from agents.ollama_api import OllamaQwen3Client
from dotenv import load_dotenv

from services.web_scraper import ScrapingTool
from utils.memory_manager import MemoryManager

load_dotenv()
ollama_client = OllamaQwen3Client()


# Initialize Memory Manager
memory_manager = MemoryManager()


# Central list of required business fields
REQUIRED_BUSINESS_FIELDS = [
    "company_name",
    "business_domain",
    "region_or_market",
    "business_needs",
    "product_or_service",
    "target_audience",
    "unique_value_proposition",
    "distribution_channels",
    "revenue_model",
    "key_partners",
    "kpis_or_outcomes",
    "technologies_involved",
    "document_references",
    "start_date",
    "urls",
]


# Updated extract_info_from_prompt function
def extract_info_from_prompt(
    prompt: str, doc_text: str = "", session_id: str = "default"
) -> dict:
    # Get conversation history
    chat_history = memory_manager.get_full_chat_history(session_id)
    long_term_mem = memory_manager.get_long_term_memory(session_id)

    # --- Per-session business info persistence logic ---
    # Use a per-session attribute to store all business fields
    if not hasattr(memory_manager, "business_info_store"):
        memory_manager.business_info_store = {}
    business_info_store = memory_manager.business_info_store
    business_fields = REQUIRED_BUSINESS_FIELDS

    final_prompt = f"""

You are a highly intelligent business analyst AI assistant with the ability to use both short-term and long-term memory to understand and extract business-relevant information.

You will receive:
- A new user prompt describing a business idea or context.
- A conversation history (short-term memory).
- A long-term memory record of past relevant business information.
- Optionally, additional documentation text.

---

### SHORT-TERM MEMORY (Conversation History)

{chat_history if chat_history else "No short-term memory yet."}

### LONG-TERM MEMORY (Persistent User Context)

{long_term_mem if long_term_mem else "No long-term memory available."}

---

### CURRENT INPUT (User Prompt)

--- START PROMPT ---
{prompt}
--- END PROMPT ---

{f"### ATTACHED DOCUMENTATION\n{doc_text}" if doc_text else "No additional documents provided."}

---

### INSTRUCTIONS

Using all available memory sources (prefer short-term, then long-term if needed), extract the following structured business information in **valid JSON** format.

**Answer in the same language as the user prompt.**

If an item is **not explicitly mentioned**, infer intelligently using memory and prompt context.
Only use `"N/A"` when information is truly unavailable or unverifiable.
For **`business_needs`**, **DO NOT leave it empty**. If not explicitly stated, deduce it based on prompt goals or implied pain points.

**For `start_date`:**
- If the prompt mentions phrases like "I want to launch", "I’m planning", "I will start", return `"planned"`.
- If it mentions "I have", "I already have", "my company currently", return `"existing"`.
- If truly unclear, return `"N/A"`.

**Additionally, extract all website URLs found anywhere in the prompt, memory, or attached documents. List them in a new field `urls` as a list of strings. Example: `"urls": ["https://example.com", "http://another.com"]`.**

Return ONLY the following structure in JSON, with no extra commentary or code blocks:

{{
    "response_code": 200,
    "data": {{
        "company_name": "...",
        "business_domain": "...",
        "region_or_market": "...",
        "business_needs": "...",  // Intelligent deduction if not mentioned
        "product_or_service": "...",
        "target_audience": "...",
        "unique_value_proposition": "...",
        "distribution_channels": "...",
        "revenue_model": "...",
        "key_partners": "...",
        "kpis_or_outcomes": "...",
        "technologies_involved": "...",
        "document_references": "...", // If applicable
        "start_date": "...", // planned, existing, or N/A
        "urls": ["..."], // List of all website URLs found and if empty don't include this field and make the offical company website the first URL in the list
        //Add any other relevant fields you find important in the prompt or memory in a similar format "key": "value" for example "CEO": "...", "other_field": "...", ...
    }}
}}

### RESPONSE CODE RULES

- Use **`"response_code": 200`** if all required fields are successfully extracted or inferred.
- Use **`"response_code": 400`** if some required information is missing and cannot be reasonably inferred.
- Use **`"response_code": 403`** if the input does not relate to business, company strategy, market analysis, product/service definition, gap/opportunity detection, or commercial insights.

### NOTES

- Be concise and precise.
- Do not speculate beyond memory and input.
- If memory contradicts prompt, defer to prompt.
- Output only the JSON object.

### IMPORTANT FILTERING RULE
- Only respond if the prompt clearly relates to **business, company strategy, market analysis, product/service definition, gap/opportunity detection, or commercial insights**.
- If the prompt is **not relevant to business/market analysis** (e.g., personal topics, programming issues, jokes, emotional support, etc.), return the following JSON object exactly:
{{
    "response_code": 403,
    "message": "Not my job — I only handle business and market-related analysis."
}}

"""

    try:
        response = ollama_client.generate(final_prompt)
        
        # Check if response is empty
        if not response or not response.strip():
            print(f"🚨 Empty response from Ollama API")
            return {
                "response_code": 503,
                "message": "AI service returned empty response. Please try again later.",
                "error": "EMPTY_RESPONSE",
                "data": {}
            }
            
        raw_text = response.strip()
        print(f"✅ Ollama response received, length: {len(raw_text)}")
    except Exception as api_error:
        print(f"🚨 Ollama API Error: {api_error}")
        # Return a fallback response when API fails
        return {
            "response_code": 503,
            "message": "AI service temporarily unavailable. Please try again later.",
            "error": "API_UNAVAILABLE",
            "data": {}
        }

    try:
        # If model returns the JSON wrapped in code block syntax
        if "```json" in raw_text:
            json_start = raw_text.find("```json") + len("```json")
            json_end = raw_text.rfind("```")
            json_str = raw_text[json_start:json_end].strip()
        else:
            json_str = raw_text.strip()

        print(f"🔍 Raw response length: {len(raw_text)}")
        print(f"🔍 JSON string to parse: '{json_str[:200]}...' (truncated)")
        
        if not json_str:
            return {
                "error": "Empty response from AI model",
                "raw_response": raw_text,
                "response_code": 500
            }

        extracted_data = json.loads(json_str)
        print(f"Extracted data: {extracted_data}")
        response_code = extracted_data.get("response_code", 100)
        if response_code == 403:
            return {
                "response_code": 403,
                "message": "Not my job — I only handle business and market-related analysis.",
            }
        # --- User Correction & Persistence Logic ---
        # Get or create per-session business info dict
        session_info = business_info_store.get(session_id, {})
        for field in business_fields:
            new_val = extracted_data.get("data", {}).get(field)
            prev_val = session_info.get(field)
            # If the prompt provides a new value (not N/A/empty), use it and update store
            if (
                new_val
                and (
                    isinstance(new_val, str)
                    and new_val.strip().upper() != "N/A"
                    and new_val.strip()
                )
                or (isinstance(new_val, list) and new_val)
            ):
                session_info[field] = new_val
            # If no new value, but previous value exists, keep previous value
            elif prev_val and (
                (
                    isinstance(prev_val, str)
                    and prev_val.strip().upper() != "N/A"
                    and prev_val.strip()
                )
                or (isinstance(prev_val, list) and prev_val)
            ):
                extracted_data["data"][field] = prev_val
        # Save updated session info
        business_info_store[session_id] = session_info
        # Update memory with the new interaction
        memory_manager.update_long_term_memory_with_prompt(session_id, prompt, raw_text)
        memory_manager.get_chat_history(session_id).add_user_message(prompt)
        memory_manager.get_chat_history(session_id).add_ai_message(raw_text)
        return extracted_data
    except json.JSONDecodeError as e:
        print(f"🚨 JSON Parse Error: {e}")
        print(f"🚨 Raw response: {raw_text[:500]}...")
        return {
            "error": "Failed to parse JSON response from AI model",
            "details": str(e),
            "raw_response": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
            "response_code": 500
        }


def detect_missing_info(extracted_info: dict) -> list[str]:
    required_fields = REQUIRED_BUSINESS_FIELDS

    missing = []

    for field in required_fields:
        value = extracted_info.get(field)

        if value is None:
            missing.append(field)
        elif isinstance(value, str) and not value.strip():
            missing.append(field)
        elif isinstance(value, list) and all(not str(item).strip() for item in value):
            missing.append(field)
        elif isinstance(value, (dict, int, float)) and not value:
            missing.append(field)

        elif isinstance(value, str) and value.strip().upper() == "N/A":
            missing.append(field)

    return missing
