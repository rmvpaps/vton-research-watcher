from processor.base_processor import BaseProcessor
from shared.models import Article,RelevanceScore
from typing import List
import asyncio
import numpy as np
from sentence_transformers import SentenceTransformer
import json 
import logging
from keybert import KeyBERT
from transformers import pipeline

class simpleTransformerProcessorError(Exception):
    pass

class simpleTransformerProcessor(BaseProcessor):
    """
    Use transformers and locally downloaded models to generate summary, keywords, semantic match with keywordlist
    """

    def __init__(self, keywords: List[str]):
        self.keywords = keywords
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')  # e.g., a SentenceTransformer instance
        self.kw_embeddings = self.model.encode(keywords)

        #keyword extraction and summary
        self.kw_model = KeyBERT(model='all-MiniLM-L6-v2')
        self.summarizer = pipeline(
                "text-generation", 
                model="facebook/bart-base", 
                device=-1 
            )
        

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
        


    async def generateSummary(self, article:Article, actualText:str)->str:
        """Generate Summary from abstract and title and actual text"""
        try:
            prompt = f"Summarize the following research text briefly:\n\n{actualText[:2000]}"
            word_count = len(actualText[:2000].split())
            calculated_max = min(50, int(word_count * 0.35))
            summary = self.summarizer(prompt, max_new_tokens=calculated_max, num_beams=2, do_sample=False,repetition_penalty=2.0)
            print(word_count,calculated_max,summary)
            return summary[0]['generated_text']
        except Exception as e:
            logging.error(f"Error in summary generation of {article.arxiv_id} {e}")
            raise simpleTransformerProcessorError("Summary generation Failed")
        

    async def generateKeywords(self, article:Article, actualText:str)->List[str]:
        """Generate Keywords from abstract,title and actual text"""
        try:
            keywords = self.kw_model.extract_keywords(actualText)
            return [k[0] for k in keywords]
        except Exception as e:
            logging.error(f"Error in keyword generation of {article.arxiv_id} {e}")
            raise simpleTransformerProcessorError("Keyword generation Failed")
        

    async def evaluate_text(self, article:Article, fullText:str)->Article:
        """Generate a summary, keep the summary vector, generate keywords from fullText"""
        try:
            keywords = await self.generateKeywords(article=article,actualText=fullText)
            summary = await self.generateSummary(article=article,actualText=fullText)
            if summary is not None:
                vector = await asyncio.to_thread(self.model.encode, summary)
            else:
                vector = await asyncio.to_thread(self.model.encode, article.abstract)
            article.summary = summary
            article.keywords = keywords
            article.embedding = vector
            enriched = Article.model_validate(article)
            return enriched
        
        except simpleTransformerProcessorError as s:
            logging.error("Error in processing full text")
            return None
        except Exception as e:
            logging.error(f"Unexpected Error occured {e}")
            raise e