import pathlib

from processor import BaseProcessor,ProcessorUtils
from shared.models import Article,RelevanceScore,Enriched
from typing import List
import asyncio
import numpy as np
import json 
import logging
from keybert import KeyBERT
from transformers import AutoConfig, T5Tokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer
import os
from shared import settings
import yake
from langchain_text_splitters import MarkdownTextSplitter

class simpleTransformerProcessorError(Exception):
    pass

class simpleTransformerProcessor(BaseProcessor):
    """
    Use transformers and locally downloaded models to generate summary, keywords, semantic match with keywordlist
    """

    def __init__(self, keywords: List[str],encoding_model:ProcessorUtils):
        if len(keywords) < 3:
            raise ValueError("At least two keywords are required to define a domain and one additional keyword.")
        self.domain = keywords[:2]
        self.keywords = keywords[2:]
        self.encoding_model = encoding_model

        self.kw_embeddings = self.encoding_model.encode(self.format_keyword_query())
        #keyword extraction and summary
        # kw_model = SentenceTransformer(
        #     settings.keybert_path, 
        #     device='cpu',
        #     local_files_only=True)
        self.kw_model = KeyBERT(model=encoding_model.model)
        clean_path = pathlib.Path(settings.summarizer_path).as_posix()
        config = AutoConfig.from_pretrained(clean_path, local_files_only=True)
        self.summarizer = T5ForConditionalGeneration.from_pretrained(
            clean_path,
            config=config,
            local_files_only=True)
        self.tokenizer = T5Tokenizer.from_pretrained(
            clean_path,
            config=config,
            local_files_only=True
        )


    def format_keyword_query(self) -> str:
        keyword_str = ", ".join(self.keywords)
        # Natural sentence template
        return (
            f"A research paper abstract in the domain of {self.domain[0]} and {self.domain[1]} "
            f"focusing on topics like {keyword_str}."
        )

    async def evaluate_abstract(self, article:Article)->RelevanceScore:
        """Match against keyword list and generate score"""
        abstract = article.abstract
        #direct match
        text = abstract.lower()
        keywords = self.keywords + self.domain
        matched = []
        for kw in keywords:
            if kw.lower() in text:
                matched.append(kw)

        matches = len(matched)
        direct_score = matches / len(keywords) if keywords else 0


        # 2. Semantic Match Score (Cosine Similarity)
        # Wrap in to_thread if using a heavy local model
        abs_embedding = await asyncio.to_thread(self.encoding_model.encode, abstract)
        
        # Calculate cosine similarity against all keywords and take the max or mean
        # Using numpy: (A dot B) / (normA * normB)
        similarities = np.dot(self.kw_embeddings, abs_embedding) / (
            np.linalg.norm(self.kw_embeddings) * np.linalg.norm(abs_embedding)
        )
        semantic_score = np.max(similarities)

        # 3. Weighted Average
        final_score =  (direct_score * 0.3) + (semantic_score * 0.7)
        rel = RelevanceScore(article_id=article.id,score=final_score,matched_keywords=json.dumps(matched))
        return rel    
        


    async def generateSummary(self, article:Article, actualText:str,short=False)->str:
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

                if short:
                    calculated_max = 20
                    calculated_min = 10
                
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
            #Language model based keyword extraction using KeyBERT
            keywords = self.kw_model.extract_keywords(actualText,keyphrase_ngram_range=(1, 1), stop_words='english',
                              use_maxsum=True, nr_candidates=20, top_n=10, use_mmr=True, diversity=0.5)

            keywords1 =  [k[0] for k in keywords]
            #Statitsical based keyword extraction using Yake
            kw_extractor = yake.KeywordExtractor(
                lan="en",           # Language
                n=3,                # Max ngram size (e.g., 1 to 3 words per phrase)
                dedupLim=0.9,       # Deduplication threshold
                top=5               # Number of keywords to return
            )

            # Extract Keywords
            keywords2 = []#kw_extractor.extract_keywords(actualText)
            #use sets to deduplicate and combine keywords from both methods
            return {k for k in keywords1 + keywords2}

        except Exception as e:
            logging.error(f"Error in keyword generation of {article.arxiv_id} {e}")
            raise simpleTransformerProcessorError("Keyword generation Failed")

    async def generateChunks(self, article:Article, actualText:str)->List[str]:
        """Generate Chunks from abstract,title and actual text"""
        try:
            markdown_paper_splitter = MarkdownTextSplitter(
                chunk_size=2048,       # Keeps text safely under BGE's 512-token ceiling
                chunk_overlap=64,
                length_function=len #TODO:tiktoken token count can be used for bge
            )
            chunks = markdown_paper_splitter.split_text(actualText)
            final_chunks = []
            #TODO: summarize each chunk and store the summary along with the chunk for better retrieval
            for chunk in chunks:
                logging.info(f"Chunk size: {len(chunk)} words {len(chunk.split())}")
                try:
                    summary = await self.generateSummary(article,chunk,short=True)
                    logging.info(f"Chunk summary: {summary}")
                    final_chunks.append(f"Part of paper discussing {article.title}. \n {summary}  \n\n {chunk}")
                except Exception as e:
                    logging.error(f"Error in processing chunk of {article.arxiv_id}: {e}")
                    final_chunks.append(chunk)

            return final_chunks

        except Exception as e:
            logging.error(f"Error in chunk generation of {article.arxiv_id}: {e}")
            raise simpleTransformerProcessorError("Chunk generation Failed")

    async def createEmbeddings(self, chunks:List[str])->List[List[float]]:
        """Generate Embeddings from chunks"""
        try:
            embeddings = await asyncio.to_thread(self.encoding_model.encode, chunks, show_progress_bar=True)
            return embeddings
        except Exception as e:
            logging.error(f"Error in embedding generation: {e}")
            raise simpleTransformerProcessorError("Embedding generation Failed")

    async def evaluate_text(self, article:Article, score:float, fullText:str)->Enriched:
        """Generate a summary, keep the summary vector, generate keywords from fullText"""
        try:
            logging.info("Processing full text")
            keywords = await self.generateKeywords(article=article,actualText=fullText)


            summary = await self.generateSummary(article=article,actualText=fullText)
            chunks = await self.generateChunks(article=article,actualText=fullText)
            enriched = Enriched(**article.model_dump(),score=score)
            enriched.summary = summary
            enriched.keywords = keywords
            enriched.chunks = chunks
            
            return enriched
        
        except simpleTransformerProcessorError as s:
            logging.error("Error in processing full text")
            return None
        except Exception as e:
            logging.error(f"Unexpected Error occured {e}")
            raise e
        