# LLM (Ollama/Qwen3) Configuration

OLLAMA_BASE_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama2:7b"

# GPU Configuration for Ollama
OLLAMA_GPU_ENABLED = True
OLLAMA_GPU_COUNT = -1  # -1 means use all available GPUs
OLLAMA_LOW_VRAM = False  # Set to True if you have limited VRAM (< 6GB)

# Common topics for topic selection (adapted for Ollama/Qwen3)
# Maps topic names to Google News RSS topic IDs
COMMON_TOPICS = {
    "top_stories": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB",
    "world": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGs0ZDZIU0FtVnVHZ0pWVXlnQVAB",
    "business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
    "technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB",
    "entertainment": "CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB",
    "sports": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB",
    "science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnVHZ0pWVXlnQVAB",
    "health": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtWnlLQUFQAQ",
    "economy": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtWnlHZ0pGVWlnQVAB",
}
