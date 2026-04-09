from scraper import BaseScraper
from scraper import HtmlScraper

class ScraperFactory:
    _scrapers = {
        "html": HtmlScraper,
        "xml": BaseScraper
    }

    @classmethod
    def get_scraper(cls, scraper_type: str, **kwargs) -> BaseScraper:
        scraper_class = cls._scrapers.get(scraper_type.lower())
        if not scraper_class:
            raise ValueError(f"Unknown scraper type: {scraper_type}")
        return scraper_class(**kwargs)