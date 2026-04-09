import pytest
import respx
import httpx

from scraper.htmlScraper import HtmlScraper
 

@pytest.mark.asyncio
async def test_fetch_ids_success():
    # 1. Setup the Mock Server using respx
    with respx.mock(base_url="https://arxiv.org") as respx_mock:
        # Define what the "fake" ArXiv should return
        
        fake_html = "<html><a title='Abstract' href='/abs/2401.12345'>...</a></html>"
        with open("list.txt", "r",encoding='utf-8') as f:
            text =  f.read()        
            fake_html = text
        respx_mock.get("/list/cs.CV/pastweek?skip=0&show=25").mock(
            return_value=httpx.Response(200, text=fake_html)
        )

        # 2. Instantiate your actual scraper
        scraper = HtmlScraper(base_url="https://arxiv.org")
        
        # 3. Use a real AsyncClient (it will be intercepted by respx)
        async with httpx.AsyncClient() as client:
            ids = await scraper.fetch_ids(client, 25)

        # 4. Assertions
        assert len(ids) == 1
        assert ids[0] == "2401.12345"