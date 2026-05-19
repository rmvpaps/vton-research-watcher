from processor import BaseProcessor,ProcessorUtils
from shared.models import Article,RelevanceScore,Enriched
from typing import List
import asyncio
import numpy as np
import json 
import logging
from keybert import KeyBERT
from transformers import T5Tokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer

from shared import settings



class simpleTransformerProcessorError(Exception):
    pass

class simpleTransformerProcessor(BaseProcessor):
    """
    Use transformers and locally downloaded models to generate summary, keywords, semantic match with keywordlist
    """

    def __init__(self, keywords: List[str],encoding_model:ProcessorUtils):
        self.keywords = keywords
        self.encoding_model = encoding_model
        self.kw_embeddings = self.encoding_model.encode(keywords)
        #keyword extraction and summary
        kw_model = SentenceTransformer(
            settings.keybert_path, 
            device='cpu',
            local_files_only=True)
        self.kw_model = KeyBERT(model=kw_model)
        self.summarizer = T5ForConditionalGeneration.from_pretrained(
            settings.summarizer_path,
            local_files_only=True)
        self.tokenizer = T5Tokenizer.from_pretrained(
            settings.summarizer_path,
            local_files_only=True
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
        abs_embedding = await asyncio.to_thread(self.encoding_model.encode, abstract)
        
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
            summarized_text = ""
            textSize = len(actualText)
            logging.info(f"Processing text of size {textSize}")
            for start in range(0,textSize,2000):
                if start==0:
                    chunk = actualText[start:start+2000]
                else:
                    chunk = actualText[start-50:start+2000]
                
                logging.info(f"Processing chunk till {start+2000}")
                prompt = f"summarize: {chunk}"
                word_count = len(chunk.split())
                calculated_max = min(50, word_count//2)
                calculated_min = min(word_count//4, 40)

                inputs = self.tokenizer.encode(
                    prompt,
                    return_tensors="pt",
                    max_length=512,
                    truncation=True
                )

                summary_ids = self.summarizer.generate(
                    inputs,
                    max_length=calculated_max,
                    min_length=calculated_min,
                    length_penalty=2.0,
                    num_beams=4,
                    early_stopping=True
                )

                summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                s_word_count = len(summary.split())
                # summary_config =  {
                #     "max_new_tokens": calculated_max,
                #     "min_length": 15,
                #     "repetition_penalty": 2.5,
                #     "do_sample": False,
                #     "pad_token_id": self.model.tokenizer.pad_token_id,
                #     "eos_token_id": self.model.tokenizer.eos_token_id,
                # }

                # summary = self.summarizer(prompt, **summary_config)
                logging.debug(f"Chunk wordcount:{word_count}, chunk summary words {s_word_count}")
                summarized_text+=summary


            #TODO: one last round on final summary if very large
            

            return summarized_text
        except Exception as e:
            logging.error(f"Error in summary generation of {article.arxiv_id} {e}")
            raise simpleTransformerProcessorError("Summary generation Failed")
        

    async def generateKeywords(self, article:Article, actualText:str)->List[str]:
        """Generate Keywords from abstract,title and actual text"""
        try:
            keywords = self.kw_model.extract_keywords(actualText,keyphrase_ngram_range=(1, 1), stop_words='english',
                              use_maxsum=True, nr_candidates=20, top_n=10)
            return [k[0] for k in keywords]
        except Exception as e:
            logging.error(f"Error in keyword generation of {article.arxiv_id} {e}")
            raise simpleTransformerProcessorError("Keyword generation Failed")
        

    async def evaluate_text(self, article:Article, score:float, fullText:str)->Enriched:
        """Generate a summary, keep the summary vector, generate keywords from fullText"""
        try:
            logging.info("Processing full text")
            keywords = await self.generateKeywords(article=article,actualText=fullText)
            summary = await self.generateSummary(article=article,actualText=fullText)
            if summary is not None:
                vector = await asyncio.to_thread(self.encoding_model.encode, summary)
            else:
                vector = await asyncio.to_thread(self.encoding_model.encode, article.abstract)

            enriched = Enriched(**article.model_dump(),score=score)
            enriched.summary = summary
            enriched.keywords = keywords
            enriched.embedding = vector
            
            return enriched
        
        except simpleTransformerProcessorError as s:
            logging.error("Error in processing full text")
            return None
        except Exception as e:
            logging.error(f"Unexpected Error occured {e}")
            raise e
        
