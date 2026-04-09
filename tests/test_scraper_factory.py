from scraper.scraper_factory import ScraperFactory
from scraper.htmlScraper import HtmlScraper
import pytest

def test_factory_returns_correct_plugin():


    scraper = ScraperFactory.get_scraper("html", base_url="http://test.com")
    assert isinstance(scraper, HtmlScraper)

def test_factory_raises_on_invalid_type():
    with pytest.raises(ValueError, match="Unknown scraper type"):
        ScraperFactory.get_scraper("invalid_mode")