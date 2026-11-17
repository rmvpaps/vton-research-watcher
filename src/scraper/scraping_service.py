from scraper import ScraperFactory
from shared import Article, article_dba
from shared.config import settings
from shared import get_session
import asyncio
import logging
import httpx
from tqdm import tqdm

logger = logging.getLogger(__name__)


class scraperService:

    def __init__(self,rate_limiter=None):
        self.scraper =ScraperFactory.get_scraper(
            settings.scraper_mode, 
            base_url=settings.baseURL,
            rate_limiter = rate_limiter
        )
 
    async def run(self, pbar_flag=False):

        print("Hello from vton-research-watcher!")
        fetch_more=True
        skip = 0
        newIDList = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            while fetch_more:
                IDList,total = await self.scraper.fetch_ids(client,settings.SCRAPE_BATCH_SIZE,skip=skip)
                if not IDList and len(IDList) == 0:
                    logger.error("No IDs recovered")
                    print("No IDs recovered")
                    fetch_more = False
                else:
                    async with get_session() as session:
                        IDList = await article_dba.removeDuplicates(session,IDList) 
                        print("Following new articles recovered",IDList)
                        if len(IDList) == 0:
                            print("No new IDs recovered")
                            logger.error("No non duplicate IDs recovered")
                            skip = skip+settings.SCRAPE_BATCH_SIZE #try next page
                        else:
                            newIDList.extend(IDList)
                            if len(newIDList)>=settings.SCRAPE_BATCH_SIZE:
                                #we got enough 
                                newIDList = newIDList[:settings.SCRAPE_BATCH_SIZE]
                                fetch_more=False
                            elif skip+settings.SCRAPE_BATCH_SIZE>=total:
                                #we have already finished
                                fetch_more=False
                            else:
                                skip = skip+settings.SCRAPE_BATCH_SIZE
                        logging.info(f"Identified {len(newIDList)} new articles to fetch")
                        #await scraper.get_details_batch(client,IDList)
                        # 2. For each ID, fetch details and save to DB
            if pbar_flag:
                with tqdm(total=len(newIDList), desc="Scraping articles") as pbar:
                    async with asyncio.TaskGroup() as tg:

                        for paper_id in newIDList:
                            logger.info("Get each article")
                            tg.create_task(self._fetch_and_store(client, paper_id,pbar=pbar))
            else:
                async with asyncio.TaskGroup() as tg:
                
                    for paper_id in newIDList:
                        logger.info("Get each article")
                        tg.create_task(self._fetch_and_store(client, paper_id))





    async def _fetch_and_store(self, client, paper_id,pbar=None):
        article = await self.scraper.fetchPaperDetails(client, paper_id)
        logger.info("Going to store fetched article")
        if article:
            async with get_session() as session:
                db_article = Article.model_validate(article)
                try:
                    await article_dba.store_results(session,db_article)
                except Exception as e:
                    logger.error(f"Error in saving article with id {article.arxiv_id}")
        if pbar:
            pbar.update(1)

