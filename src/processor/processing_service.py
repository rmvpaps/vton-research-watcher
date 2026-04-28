from shared import Article,settings,fetch_next_batch,get_session,updateArticle
import httpx
from processor import ProcessorFactory,simpleFullTextExtractor
from typing import List
import logging


keyword_list = [
    "Reconstruction",
    "Photogrammetry",
    "Human Parametric Model",
    "multi-view synchronization",
    "Virtual Try On",
    "3DGS"
    
]

class ProcessingService:
    """
    Class that orchestrates simple abstract processing, deep text processing, vector storage
    """
    def __init__(self):
        self.processor = ProcessorFactory.get_processor(settings.processor_mode,keywords=keyword_list)
        self.downloader = simpleFullTextExtractor()


    async def fetch_next_batch_and_process(self,session)->List[Article]:
        """
        Function to fetch unprocessed articles from DB
        """
        async with get_session() as session:
            articles = await fetch_next_batch(session,5)

            for article in articles:
                await self.process_article(session,article)



    async def process_article(self, session, article: Article):
        
        # 2. PASS 1: Abstract Analysis
        # Returns a score and a 'is_relevant' boolean based on your threshold
        result = await self.processor.evaluate_abstract(article)
        
        if result.score < 0.5:
            article.processed = True
            article.status = 'rejected'
            await updateArticle(session,article)
            logging.info(f"Rejecting artice {article.arxiv_id} as score is less - {result.score}")
            return


        full_text = await self.downloader.download_get_text(article.arxiv_id)
        
        # 4. ENRICHMENT & VECTORIZATION
        enriched_data = await self.processor.evaluate_text(article, full_text)
        
        
        # 5. FINAL STORAGE
        # await updateKeywords(enriched_data.keywords)
        # await updateEmbeddings(enriched_data.embedding)

        article.summary = enriched_data.summary
        article.processed = True
        article.status = 'indexed'
        await updateArticle(session,article)