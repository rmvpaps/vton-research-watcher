from processor.base_processor import BaseProcessor
from shared.models import Article,RelevanceScore
from typing import List
import asyncio
import numpy as np
from sentence_transformers import SentenceTransformer
import json 

class simpleTransformerProcessor(BaseProcessor):
    """
    Use transformers and locally downloaded models to generate summary, keywords, semantic match with keywordlist
    """

    def __init__(self, keywords: List[str]):
        self.keywords = keywords
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')  # e.g., a SentenceTransformer instance
        # Pre-calculate keyword embeddings to save time
        self.kw_embeddings = self.model.encode(keywords)

    async def evaluate_abstract(self, article:Article)->RelevanceScore:
        """Match against keyword list and generate score"""
        abstract = article.abstract
        #direct match
        text = abstract.lower()
        matched = []
        for kw in self.keywords:
            if kw.lower() in text:
                matched.append(kw)

        matches = len(matched)
        direct_score = matches / len(self.keywords) if self.keywords else 0


        # 2. Semantic Match Score (Cosine Similarity)
        # Wrap in to_thread if using a heavy local model
        abs_embedding = await asyncio.to_thread(self.model.encode, abstract)
        
        # Calculate cosine similarity against all keywords and take the max or mean
        # Using numpy: (A dot B) / (normA * normB)
        similarities = np.dot(self.kw_embeddings, abs_embedding) / (
            np.linalg.norm(self.kw_embeddings, axis=1) * np.linalg.norm(abs_embedding)
        )
        semantic_score = np.max(similarities)

        # 3. Weighted Average
        final_score =  (direct_score * 0.3) + (semantic_score * 0.7)
        rel = RelevanceScore(article_id=article.id,score=final_score,matched_keywords=json.dumps(matched))
        return rel