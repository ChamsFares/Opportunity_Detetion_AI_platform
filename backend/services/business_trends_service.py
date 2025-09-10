from agents.BusinessTrends import BusinessTrends
from agents.ollama_api import OllamaQwen3Client
from services.web_scraper import ScrapingTool

# Initialize Ollama client
ollama_client = OllamaQwen3Client()

def generate_text(prompt: str) -> str:
    """Generate text using Ollama client"""
    try:
        response = ollama_client.generate(prompt, max_tokens=1000)
        return response.strip()
    except Exception as e:
        print(f"Error generating text with Ollama: {e}")
        return ""

MAX_TOKENS = 800_000


def estimate_token_count(text: str) -> int:
    # Rough estimate: 1 token ≈ 4 characters (for English)
    return len(text) // 4


def summarize_page_content(content: str) -> tuple[str, str]:
    if not content:
        return "No content to summarize.", "No trend detected."

    summary_prompt = (
        f"Summarize the following content strictly based on what is written. "
        f"Do not add external knowledge, assumptions, or commentary. "
        f"Respond with only the summary — no headers, introductions, or explanations.\n\n{content}"
    )

    trend_prompt = (
        f"From the following content, extract the main business or market trend mentioned. "
        f"Respond with one clear sentence only. Do not guess or add external info. "
        f"Do not include any intro or explanation — only return the sentence.\n\n{content}"
    )

    summary = generate_text(summary_prompt)
    trend = generate_text(trend_prompt)

    return summary, trend


def get_domain_trends_results(domain: str):
    agent = BusinessTrends(generate_text, ScrapingTool())
    results = agent.run(domain)

    summarized_results = []
    total_tokens = 0

    for page in results:
        content = page.get("content", "")
        url = page.get("url", "")

        summary, trend = summarize_page_content(content)

        tokens = estimate_token_count(summary)
        if total_tokens + tokens > MAX_TOKENS:
            break

        page_summary = {
            "url": url,
            "title": page.get("title", ""),
            "summary": summary,
            "trend": trend,
            "found_internal_urls": page.get("found_internal_urls", []),
            "depth": page.get("depth", None),
        }

        summarized_results.append(page_summary)
        total_tokens += tokens

    return {
        "summarized_results": summarized_results,
        "total_tokens": total_tokens,
        "token_limit": MAX_TOKENS,
    }
