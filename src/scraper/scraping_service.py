from scraper import ScraperFactory
from shared import Article, article_dba
from shared.config import settings
from shared import get_session
import asyncio
import logging
import httpx

class scraperService:

    def __init__(self,rate_limiter=None):
        self.scraper =ScraperFactory.get_scraper(
            settings.scraper_mode, 
            base_url=settings.baseURL,
            rate_limiter = rate_limiter
        )
 
    async def run(self):

        print("Hello from vton-research-watcher!")
        async with httpx.AsyncClient(timeout=10.0) as client:
            IDList = await self.scraper.fetch_ids(client,65)
            if not IDList and len(IDList) == 0:
                logging.error("No IDs recovered")
                print("No IDs recovered")
            else:
                async with get_session() as session:
                    IDList = await article_dba.removeDuplicates(session,IDList) 
                    print("Following new articles recovered",IDList)
                    if len(IDList) == 0:
                        print("No new IDs recovered")
                        logging.error("No non duplicate IDs recovered")
                    else:
                        #await scraper.get_details_batch(client,IDList)
                        # 2. For each ID, fetch details and save to DB
                        async with asyncio.TaskGroup() as tg:
                            for paper_id in IDList:
                                tg.create_task(self._fetch_and_store(client, paper_id))




    async def _fetch_and_store(self, client, paper_id):
        article = await self.scraper.fetchPaperDetails(client, paper_id)
        if article:
            async with get_session() as session:
                db_article = Article.model_validate(article)
                try:
                    await article_dba.store_results(session,db_article)
                except Exception as e:
                    logging.error(f"Error in saving article with id {article.arxiv_id}")

