import asyncio
import json
import logging
import os
from typing import Optional

from agents.ollama_api import OllamaQwen3Client
import nltk
from langdetect import LangDetectException, detect
from nltk.corpus import stopwords

from agents.summarization_agent import summarization_agent
from services.web_scraper import crawl_website
from utils.crawled_info_saver import save_crawled_company
from utils.memory_manager import MemoryManager

# Download NLTK stopwords if not already present
try:
    stopwords.words("english")
except LookupError:
    nltk.download("stopwords")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("top_competitors")
ollama_client = OllamaQwen3Client()
memory_manager = MemoryManager()


async def extract_company_info_llm(input_json: dict) -> dict:
    """
    Uses the LLM to extract and normalize company info into the required format from any input JSON.
    Returns a dict with the following keys:
        company_name, business_domain, region_or_market, business_needs, product_or_service, target_audience,
        unique_value_proposition, distribution_channels, revenue_model, key_partners, kpis_or_outcomes,
        technologies_involved, document_references, start_date, urls
    """
    extraction_prompt = (
        "You are an information extraction AI. Given the following JSON, extract and return only the following fields in a JSON object, using the best available information from the input. "
        "If a field is missing, use 'N/A'. The output must be a valid JSON object with exactly these keys and no extra text.\n\n"
        "Fields to extract:\n"
        "- company_name\n- business_domain\n- region_or_market\n- business_needs\n- product_or_service\n- target_audience\n- unique_value_proposition\n- distribution_channels\n- revenue_model\n- key_partners\n- kpis_or_outcomes\n- technologies_involved\n- document_references\n- start_date\n- urls\n\n"
        f"Input JSON:\n{json.dumps(input_json, ensure_ascii=False)}\n"
        "Output:"
    )
    try:
        response = await asyncio.to_thread(ollama_client.generate, extraction_prompt)
        raw_text = response.strip()
        if "```json" in raw_text:
            json_start = raw_text.find("```json") + len("```json")
            json_end = raw_text.rfind("```")
            json_str = raw_text[json_start:json_end].strip()
        else:
            json_str = raw_text
        extracted = json.loads(json_str)
        return extracted
    except Exception as e:
        logger.error(f"[extract_company_info_llm] Extraction failed: {e}")
        return {"error": str(e)}


async def detect_top_competitors(
    company_info: dict,
    session_id: Optional[str] = "default",
    companies_count: int = 5,
) -> dict:

    # Use LLM to extract and normalize company info first
    normalized_info = await extract_company_info_llm(company_info)
    prompt = (
        f"You are a competitive intelligence AI. List the {companies_count} most relevant and well-known competitors for the following company, operating in the same business domain and region. "
        "For each competitor, provide:\n- The full company name\n- The official company website (must be a valid URL, e.g., https://www.example.com)\n\n"
        f"Here is the company info JSON:\n{json.dumps(normalized_info, ensure_ascii=False)}\n\n"
        "Return only a JSON object in the following format:\n"
        '{"data": [{"company": "Company Name", "website": "https://..."}, ...]}\n'
        f"The data array must contain exactly {companies_count} entries. Do not include placeholders or explanations. Only output the JSON object."
    )
    try:
        response = await asyncio.to_thread(ollama_client.generate, prompt)
        raw_text = response.strip()
        # Extract JSON from response
        if "```json" in raw_text:
            json_start = raw_text.find("```json") + len("```json")
            json_end = raw_text.rfind("```")
            json_str = raw_text[json_start:json_end].strip()
        else:
            json_str = raw_text
        competitors_data = json.loads(json_str)
        logger.info("GERRRRRRRRR:", competitors_data)
        memory_manager.update_long_term_memory(session_id, prompt, raw_text)

        allowed_langs = {"en", "fr", "ar"}
        for idx, entry in enumerate(competitors_data.get("data", []), 1):
            url = entry.get("website")
            name = entry.get("company")
            logger.info(f"[{idx}] Crawling: {name} ({url})")
            if url and url.startswith("http"):
                try:
                    raw_scraped = crawl_website(url)
                    filtered_scraped = {}
                    if isinstance(raw_scraped, dict):
                        for k, v in raw_scraped.items():
                            text = v.get("content") or v.get("text_sample") or ""
                            try:
                                lang = detect(text)
                            except LangDetectException:
                                lang = v.get("detected_language", "unknown")
                            if lang in allowed_langs:
                                # Remove stopwords from content/text_sample
                                stop_words = set()
                                if lang == "en":
                                    stop_words = set(stopwords.words("english"))
                                elif lang == "fr":
                                    stop_words = set(stopwords.words("french"))
                                elif lang == "ar":
                                    stop_words = set(stopwords.words("arabic"))

                                # Remove stopwords from content
                                def remove_stopwords(text):
                                    import re

                                    words = re.findall(r"\w+", text, flags=re.UNICODE)
                                    filtered = [
                                        w for w in words if w.lower() not in stop_words
                                    ]
                                    removed_count = len(words) - len(filtered)
                                    return " ".join(filtered), removed_count

                                v_clean = v.copy()
                                removed_total = 0
                                if "content" in v:
                                    cleaned, removed = remove_stopwords(v["content"])
                                    v_clean["content"] = cleaned
                                    removed_total += removed
                                if "text_sample" in v:
                                    cleaned, removed = remove_stopwords(
                                        v["text_sample"]
                                    )
                                    v_clean["text_sample"] = cleaned
                                    removed_total += removed
                                v_clean["removed_stopwords_count"] = removed_total
                                filtered_scraped[k] = v_clean
                            else:
                                logger.info(
                                    f"[lang-skip] Skipped link {k} (lang={lang}) for {name}"
                                )
                    else:
                        filtered_scraped = raw_scraped

                    # Add summarization after processing the crawled data
                    logger.info(f"[{idx}] Summarizing crawled data for: {name}")
                    try:
                        summary = await summarization_agent.summarize_crawled_data(
                            filtered_scraped, name
                        )
                        entry["business_summary"] = summary
                        logger.info(f"[{idx}] Summary generated for: {name}")

                        # Save business summary to database
                        try:
                            save_result = await save_crawled_company(
                                company_name=name,
                                business_summary=summary,
                                website_url=url,
                            )
                            if save_result.get("success"):
                                action = save_result.get("action", "saved")
                                mongo_id = save_result.get("mongo_id", "unknown")

                                # Log MongoDB operation
                                logger.info(
                                    f"[{idx}] MongoDB: Business summary {action} for {name} (ID: {mongo_id})"
                                )

                                # Log embedding operation
                                embedding_op = save_result.get(
                                    "embedding_operation", {}
                                )
                                if embedding_op.get("success"):
                                    dimensions = embedding_op.get(
                                        "embedding_dimensions", "unknown"
                                    )
                                    logger.info(
                                        f"[{idx}] Embedding: Generated {dimensions}D vector for {name}"
                                    )
                                else:
                                    logger.warning(
                                        f"[{idx}] Embedding: Failed for {name} - {embedding_op.get('error', 'unknown error')}"
                                    )

                                # Log ChromaDB operation
                                chroma_op = save_result.get("chroma_operation", {})
                                if chroma_op and chroma_op.get("success"):
                                    logger.info(
                                        f"[{idx}] ChromaDB: Successfully stored embedding for {name}"
                                    )
                                elif chroma_op:
                                    logger.warning(
                                        f"[{idx}] ChromaDB: Failed for {name} - {chroma_op.get('error', 'unknown error')}"
                                    )
                                else:
                                    logger.warning(
                                        f"[{idx}] ChromaDB: Operation not attempted for {name}"
                                    )

                                # Store enhanced save result in entry for reference
                                entry["save_result"] = save_result
                            else:
                                logger.warning(
                                    f"[{idx}] Failed to save business summary for {name}: {save_result.get('error', 'Unknown error')}"
                                )
                                entry["save_result"] = save_result
                        except Exception as save_exc:
                            logger.error(
                                f"[{idx}] Error saving business summary for {name}: {save_exc}"
                            )
                            entry["save_result"] = {
                                "success": False,
                                "error": str(save_exc),
                            }

                    except Exception as summary_exc:
                        entry["business_summary"] = {
                            "error": f"Summarization failed: {str(summary_exc)}"
                        }
                        logger.error(f"[{idx}] Error summarizing {name}: {summary_exc}")

                    entry["scraped data"] = filtered_scraped
                    logger.info(f"[{idx}] Done: {name}")
                except Exception as crawl_exc:
                    entry["scraped data"] = {"error": str(crawl_exc)}
                    entry["business_summary"] = {
                        "error": "Could not generate summary due to crawling failure"
                    }
                    logger.error(f"[{idx}] Error crawling {name}: {crawl_exc}")
            else:
                entry["scraped data"] = {"error": "Invalid or missing URL"}
                entry["business_summary"] = {
                    "error": "Could not generate summary due to invalid URL"
                }
                logger.warning(f"[{idx}] Skipping invalid URL for {name}: {url}")

        logger.info("Crawling complete.")

        # Generate overall competitors overview
        logger.info("Generating competitors overview...")
        try:
            competitors_overview = summarization_agent.generate_competitors_overview(
                competitors_data.get("data", [])
            )
            logger.info(
                f"Analysis complete: {competitors_overview['successfully_analyzed']}/{competitors_overview['total_competitors']} competitors successfully analyzed"
            )

            return {
                "data": competitors_data.get("data", []),
                "overview": competitors_overview,
            }
        except Exception as overview_exc:
            logger.error(f"Error generating overview: {overview_exc}")
            return {
                "data": competitors_data.get("data", []),
                "overview_error": str(overview_exc),
            }
    except Exception as e:
        return {"data": [], "error": str(e)}
