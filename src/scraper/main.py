from scraper import ScraperFactory, scraperService,RateLimiterFactory
from shared.config import settings
from shared import article_dba, get_session
import asyncio
import logging
import httpx

logger = logging.getLogger("ArxivWatcher")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

async def main():

    #ratelim = RateLimiterFactory.get_rate_limiter('window',rate=settings.scrape_window_rate_min)
    
    ratelim = RateLimiterFactory.get_rate_limiter('delay',delay=settings.scrape_delay_seconds)
    
    service = scraperService(ratelim)
    await  service.run()


if __name__ == "__main__":
    asyncio.run(main())
