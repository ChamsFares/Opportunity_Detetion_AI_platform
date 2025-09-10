
import requests
from config.llm_config import OLLAMA_BASE_URL, OLLAMA_MODEL, COMMON_TOPICS, OLLAMA_GPU_ENABLED, OLLAMA_GPU_COUNT, OLLAMA_LOW_VRAM

class OllamaQwen3Client:
    def __init__(self,):
        self.base_url =OLLAMA_BASE_URL
        self.model =OLLAMA_MODEL

    def generate(self, prompt, stream=False, use_gpu=None, **kwargs):
        # Use GPU settings from config if not specified
        if use_gpu is None:
            use_gpu = OLLAMA_GPU_ENABLED
            
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream
        }
        
        # Add GPU-specific options if available
        if use_gpu:
            payload.update({
                "options": {
                    "use_mmap": True,        # Memory mapping for better performance
                    "use_mlock": True,       # Lock memory to prevent swapping
                    "num_gpu": OLLAMA_GPU_COUNT,  # Use configured GPU count
                    "num_thread": 0,         # Let Ollama determine optimal thread count
                    "low_vram": OLLAMA_LOW_VRAM,  # Use configured VRAM setting
                }
            })
        
        payload.update(kwargs)
        response = requests.post(self.base_url, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")

    def specify_topics(self, sector_name, common_topics=None):
        """Ask Qwen3 to select relevant topics for a sector. Returns a list of dicts with topic_name and topic_key."""
        topics = common_topics if common_topics is not None else COMMON_TOPICS
        
        # Create a list of topic names for the LLM prompt
        topic_names = list(topics.keys()) if isinstance(topics, dict) else topics
        
        prompt = (
            f"Select among these topics the most relevant and related ones directly or indirectly that could affect or impact the {sector_name} sector. "
            f"Return a JSON list of topic names only. Topics: {topic_names}"
        )
        response = self.generate(prompt)
        import json
        try:
            selected_topic_names = json.loads(response)
            if isinstance(selected_topic_names, list):
                # Convert topic names to topic_name/topic_key format
                result = []
                for topic_name in selected_topic_names:
                    if topic_name in topics:
                        result.append({
                            "topic_name": topic_name,
                            "topic_key": topics[topic_name]
                        })
                return {"selected_topics": result}
        except Exception:
            pass
        return {"selected_topics": []}

    def summarize(self, newstitle, description):
        """Summarize a news description using Qwen3."""
        prompt = (
            f"You are a helpful assistant that summarizes this news description by capturing the important and helpful infos that will be later utilized in market studies, risk assessment and opportunities detections use cases. "
            f"***The summary does not pass 5 lines.*** The news title is {newstitle}. Make sure that you are remaining in the same language as the description. Return just the summary, no other or additional text.\n\nDescription: {description}"
        )
        return self.generate(prompt)
