import json
import httpx
from typing import Dict, Any
from openai import AsyncOpenAI # Standard client works for Groq/Together
from processor import BaseProcessor
from typing import List
import logging
from shared import Article,RelevanceScore
class HostedLLMProcessor(BaseProcessor):

    def __init__(self, keywords: List[str], api_key: str, provider_url: str ):
        self.model = "llama-3.1-8b-instant"
        self.keywords = keywords
        self.client = AsyncOpenAI(api_key=api_key, base_url=provider_url)


    async def evaluate_abstract(self, article:Article) -> RelevanceScore:
        # Defining a strict rubric ensures the 'relevance_score' isn't random
        system_prompt = (
            "You are a technical research assistant specializing in 3D Reconstruction. "
            "Evaluate abstracts based on keywords. Respond ONLY in JSON."
        )
        
        user_content = f"""
        Keywords: {', '.join(self.keywords)}
        Abstract: {article.abstract}

        Task: Rate relevance from 0.0 to 1.0. 
        - 1.0: Topic is related to most of the keywords mentioned
        - 0.6: Topic related to few of the keywords mentioned
        - 0.0: Unrelated to the given keywords(e.g., social sciences, biology, ).

        Output JSON: {{"relevance_score": float, "reasoning": "str", "is_relevant": bool}}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.1 # Keep it deterministic
            )
            result =  json.loads(response.choices[0].message.content)
            return RelevanceScore(article_id=article.id,score=result["relevance_score"],reasoning=result["reasoning"])
        except Exception as e:
            logging.error(f"LLM Evaluation failed: {e}")
            # Fallback to a neutral score so the system doesn't crash
            return RelevanceScore(article_id=article.id,score=0.0,reasoning="Error in processing")