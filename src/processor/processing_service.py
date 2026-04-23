from shared import Article,settings,fetch_next_batch,get_session,updateArticle

from processor import ProcessorFactory
from typing import List

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

        self.vector_db = vector_store      


    async def fetch_next_batch_and_process(self,session)->List[Article]:
        """
        Function to fetch unprocessed articles from DB
        """
        async with get_session() as session:
            articles = await fetch_next_batch(session,10)
            for article in articles:
                await self.process_article(session,article)


    async def process_article(self, session, article: Article):
        
        # 2. PASS 1: Abstract Analysis
        # Returns a score and a 'is_relevant' boolean based on your threshold
        result = await self.processor.evaluate_abstract(article.abstract,keyword_list)
        
        if result['score'] < 0.7:
            article.processed = True
            article.status = 'rejected'
            await updateArticle(session,Article)
            return

        # # 3. PASS 2: Full Text Expansion
        # # Only triggered if Pass 1 succeeds
        # full_text = await self.downloader.get_full_text(article.pdf_url)
        
        # # 4. ENRICHMENT & VECTORIZATION
        # # Summarize the full text and get a high-quality embedding
        # enriched_data = await self.processor.evaluate_full_text(full_text)
        
        # # 5. FINAL STORAGE
        # await self.vector_db.upsert(
        #     id=article_id,
        #     vector=enriched_data['embedding'],
        #     metadata={**enriched_data['summary'], "title": article.title}
        # )
        
        article.processed = True
        article.status = 'indexed'
        await updateArticle(session,Article)