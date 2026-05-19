from abc import ABC, abstractmethod
from typing import List
from shared import Article,RelevanceScore,Enriched,settings # Your Pydantic model
from markitdown import MarkItDown
import logging
from io import BytesIO
import httpx
from sentence_transformers import SentenceTransformer,models
import os
class BaseProcessor(ABC):

    @abstractmethod
    async def evaluate_abstract(self, article:Article)->RelevanceScore:
        """Match against keyword list and generate score"""
        pass

    @abstractmethod
    async def evaluate_text(self, article:Article,fullText:str)->Enriched:
        """Generate a summary, keep the summary vector, generate keywords from fullText"""
        pass

    # @abstractmethod
    # async def generateSummary(self, article:Article, actualText:str)->str:
    #     """Generate Summary from abstract and title and actual text and update Article in-place"""
    #     pass

    # @abstractmethod
    # async def generateKeywords(self, article:Article, actualText:str)->List[str]:
    #     """Generate Keywords from abstract,title and actual text and return the list"""
    #     pass
    


def manual_model_load(model_path):
    logging.info(f"Manually loading BGE Pipeline from: {model_path}")
    word_embedding_model = models.Transformer(model_path)

    # 2. Load the Pooling layer pointing to the subfolder "1_Pooling"
    pooling_path = os.path.join(model_path, "1_Pooling")
    pooling_model = models.Pooling(pooling_path)

    # 3. Load the Normalize layer (which requires no path config as it applies a mathematical function)
    normalize_model = models.Normalize()

    # 4. Bind them sequentially into the pipeline
    model = SentenceTransformer(modules=[
        word_embedding_model, 
        pooling_model, 
        normalize_model
    ])
    logging.info(f"successfully loaded BGE Pipeline from: {model_path}")
    return model


class ProcessorUtils:
    def __init__(self):
        self.md = MarkItDown()   
        try:
            self.model = SentenceTransformer(
                settings.embedding_path, 
                device='cpu',
                local_files_only=True)  # e.g., a SentenceTransformer instance
        except Exception as e:
            logging.error(f"Loading directly from path {settings.embedding_path} failed {e}")
            logging.warning("Attempting manual load")
            self.model = manual_model_load(settings.embedding_path)

    def encode(self,data, **kwargs):
        """
        Encode into vector
        """    
        return self.model.encode(data,**kwargs)
    
    async def download_get_text(self,id)->str:
        """
        Download the full arxiv paper
        """
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                raw = await client.get(f"{settings.ARXIV_PDF_URL}{id}")

                result = self.md.convert(BytesIO(raw.content))
            
                # This gives you the clean Markdown text
                full_text = result.text_content

                return full_text

            except Exception as e:
                logging.error(f"Error in getting and extracting ARxiv PDF {id}: {e}")
                return None
