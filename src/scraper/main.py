from scraper import ScraperFactory, removeDuplicates
from shared.config import settings
import asyncio
import logging
import httpx

logger = logging.getLogger("ArxivWatcher")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

async def main():

    print("Hello from vton-research-watcher!")
    scraper = ScraperFactory.get_scraper(
        settings.scraper_mode, 
        base_url=settings.baseURL
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        IDList = await scraper.fetch_ids(client,25)
        if not IDList and len(IDList) == 0:
            logging.error("No IDs recovered")
            print("No IDs recovered")
        else:
            IDList = await removeDuplicates(IDList) 
            print("Following new articles recovered",IDList)
            if len(IDList) == 0:
                print("No new IDs recovered")
                logging.error("No non duplicate IDs recovered")
            else:
                await scraper.get_details_batch(client,IDList)

if __name__ == "__main__":
    asyncio.run(main())
