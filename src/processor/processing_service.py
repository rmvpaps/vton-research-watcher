from shared import Article,settings,fetch_next_batch,get_session,updateArticle
import httpx
from processor import ProcessorFactory
from typing import List
import logging
from markitdown import MarkItDown

keyword_list = [
    "3D Reconstruction",
    "Photogrammetry",
    "Human Parametric Model"
]

class ProcessingService:
    """
    Class that orchestrates simple abstract processing, deep text processing, vector storage
    """
    def __init__(self, processor_plugin, db_repo, vector_store):
        self.processor = ProcessorFactory.get_processor(settings.processor_mode)
        self.md = MarkItDown()   


    async def fetch_next_batch_and_process(self,session)->List[Article]:
        """
        Function to fetch unprocessed articles from DB
        """
        async with get_session() as session:
            articles = await fetch_next_batch(session,10)

            for article in articles:
                await self.process_article(session,article)

    async def download_get_text(self,id)->str:
        """
        Download the full arxiv paper
        """
        try:

            result = self.md.convert(f"{settings.ARXIV_PDF_URL}{id}")
        
            # This gives you the clean Markdown text
            full_text = result.text_content

            return full_text

        except Exception as e:
            logging.error(f"Error in getting and extracting ARxiv PDF {id}: {e}")
            return None



    async def process_article(self, session, client, article: Article):
        
        # 2. PASS 1: Abstract Analysis
        # Returns a score and a 'is_relevant' boolean based on your threshold
        result = await self.processor.evaluate_abstract(article.abstract,keyword_list)
        
        if result['score'] < 0.7:
            article.processed = True
            article.status = 'rejected'
            await updateArticle(session,Article)
            return


        full_text = await self.download_get_text(article.arxiv_id)
        
        # 4. ENRICHMENT & VECTORIZATION
        enriched_data = await self.processor.evaluate_full_text(full_text)
        
        # 5. FINAL STORAGE

        
        article.processed = True
        article.status = 'indexed'
        await updateArticle(session,Article)