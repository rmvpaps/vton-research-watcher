import pytest
import respx
import httpx

from scraper.htmlScraper import HtmlScraper
 
@pytest.mark.asyncio
async def test_fetch_ids_nopaging(valid_arxiv_list):
    # 1. Setup the Mock Server using respx
    with respx.mock(base_url="https://arxiv.org") as respx_mock:

        

        respx_mock.get("/list/cs.CV/pastweek?skip=0&show=25").mock(
            return_value=httpx.Response(200, text=valid_arxiv_list)
        )


        # 2. Instantiate your actual scraper
        scraper = HtmlScraper(base_url="https://arxiv.org")
    
        # 3. Use a real AsyncClient (it will be intercepted by respx)
        async with httpx.AsyncClient() as client:
            ids = await scraper.fetch_ids(client, 25)

        # 4. Assertions
        assert len(ids) == 25
        assert ids[0] == "2603.30045"



@pytest.mark.asyncio
async def test_fetch_ids_paging(valid_arxiv_list):
    # 1. Setup the Mock Server using respx
    with respx.mock(base_url="https://arxiv.org") as respx_mock:

    

        respx_mock.get("/list/cs.CV/pastweek?skip=0&show=25").mock(
            return_value=httpx.Response(200, text=valid_arxiv_list)
        )
        respx_mock.get("/list/cs.CV/pastweek?skip=25&show=25").mock(
            return_value=httpx.Response(200, text=valid_arxiv_list)
        )

        # 2. Instantiate your actual scraper
        scraper = HtmlScraper(base_url="https://arxiv.org")
    
        # 3. Use a real AsyncClient (it will be intercepted by respx)
        async with httpx.AsyncClient() as client:
            ids = await scraper.fetch_ids(client, 50)

        # 4. Assertions
        assert len(ids) == 50
        assert ids[0] == "2603.30045"



@pytest.mark.asyncio
async def test_fetch_ids_paging_limitlesstotal(valid_arxiv_list):
    # 1. Setup the Mock Server using respx
    with respx.mock(base_url="https://arxiv.org") as respx_mock:

        respx_mock.get("/list/cs.CV/pastweek?skip=0&show=25").mock(
            return_value=httpx.Response(200, text=valid_arxiv_list)
        )
        respx_mock.get("/list/cs.CV/pastweek?skip=25&show=25").mock(
            return_value=httpx.Response(200, text=valid_arxiv_list)
        )
        respx_mock.get("/list/cs.CV/pastweek?skip=50&show=25").mock(
            return_value=httpx.Response(200, text=valid_arxiv_list)
        )

        
        # 2. Instantiate your actual scraper
        scraper = HtmlScraper(base_url="https://arxiv.org")
    
        # 3. Use a real AsyncClient (it will be intercepted by respx)
        async with httpx.AsyncClient() as client:
            ids = await scraper.fetch_ids(client, 60)

        # 4. Assertions
        assert len(ids) == 60
        assert ids[0] == "2603.30045"



@pytest.mark.asyncio
async def test_fetch_ids_paging_limithightotal(valid_arxiv_list):
    # 1. Setup the Mock Server using respx
    with respx.mock(base_url="https://arxiv.org") as respx_mock:

        

            
        respx_mock.get("/list/cs.CV/pastweek?skip=0&show=25").mock(
            return_value=httpx.Response(200, text=valid_arxiv_list)
        )
        respx_mock.get("/list/cs.CV/pastweek?skip=25&show=25").mock(
            return_value=httpx.Response(200, text=valid_arxiv_list)
        )
        respx_mock.get("/list/cs.CV/pastweek?skip=50&show=25").mock(
            return_value=httpx.Response(200, text=valid_arxiv_list)
        )

        # 2. Instantiate your actual scraper
        scraper = HtmlScraper(base_url="https://arxiv.org")
    
        # 3. Use a real AsyncClient (it will be intercepted by respx)
        async with httpx.AsyncClient() as client:
            ids = await scraper.fetch_ids(client, 90)

        # 4. Assertions
        assert len(ids) == 75
        assert ids[0] == "2603.30045"

@pytest.mark.asyncio
async def test_fetch_ids_paging_partial_error(valid_arxiv_list,invalid_arxiv_list):
    """
    Handles working pages even if some pages give error
    """
    # 1. Setup the Mock Server using respx
    with respx.mock(base_url="https://arxiv.org") as respx_mock:

        

       
        fake_html = valid_arxiv_list
        respx_mock.get("/list/cs.CV/pastweek?skip=0&show=25").mock(
            return_value=httpx.Response(200, text=fake_html)
        )

        respx_mock.get("/list/cs.CV/pastweek?skip=25&show=25").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

      
        fake_html = invalid_arxiv_list
        respx_mock.get("/list/cs.CV/pastweek?skip=50&show=25").mock(
            return_value=httpx.Response(200, text=fake_html)
        )

        # 2. Instantiate your actual scraper
        scraper = HtmlScraper(base_url="https://arxiv.org")
    
        # 3. Use a real AsyncClient (it will be intercepted by respx)
        async with httpx.AsyncClient() as client:
            ids = await scraper.fetch_ids(client, 90)

            # 4. Assertions
            assert len(ids) == 25
            assert ids[0] == "2603.30045"


# ── fetchPaperDetails ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_paper_details_valid(valid_arxiv_abstract):
    with respx.mock(base_url="https://arxiv.org") as respx_mock:
        respx_mock.get("/abs/2603.30045").mock(
            return_value=httpx.Response(200, text=valid_arxiv_abstract)
        )

        scraper = HtmlScraper(base_url="https://arxiv.org")

        async with httpx.AsyncClient() as client:
            article = await scraper.fetchPaperDetails(client, "2603.30045")

        assert article.arxiv_id == "2603.30045"
        assert len(article.title) > 0
        assert len(article.abstract) > 0


@pytest.mark.asyncio
async def test_fetch_paper_details_http_error(valid_arxiv_abstract):
    """Returns None (or raises) when server returns 500"""
    with respx.mock(base_url="https://arxiv.org") as respx_mock:
        respx_mock.get("/abs/2603.30045").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        scraper = HtmlScraper(base_url="https://arxiv.org")

        async with httpx.AsyncClient() as client:
            article = await scraper.fetchPaperDetails(client, "2603.30045")

        assert article is None


@pytest.mark.asyncio
async def test_fetch_paper_details_malformed_html(invalid_arxiv_abstract):
    """Returns None when HTML is missing expected fields"""
    with respx.mock(base_url="https://arxiv.org") as respx_mock:
        respx_mock.get("/abs/2603.30045").mock(
            return_value=httpx.Response(200, text=invalid_arxiv_abstract)
        )

        scraper = HtmlScraper(base_url="https://arxiv.org")

        async with httpx.AsyncClient() as client:
            article = await scraper.fetchPaperDetails(client, "2603.30045")

        assert article is None


@pytest.mark.asyncio
async def test_fetch_paper_details_404():
    """Returns None on 404"""
    with respx.mock(base_url="https://arxiv.org") as respx_mock:
        respx_mock.get("/abs/9999.99999").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        scraper = HtmlScraper(base_url="https://arxiv.org")

        async with httpx.AsyncClient() as client:
            article = await scraper.fetchPaperDetails(client, "9999.99999")

        assert article is None


# ── get_details_batch ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_details_batch_all_valid(valid_arxiv_abstract):
    """All IDs resolve successfully"""
    ids = ["2603.30045", "2603.30046", "2603.30047"]

    with respx.mock(base_url="https://arxiv.org") as respx_mock:
        for id in ids:
            respx_mock.get(f"/abs/{id}").mock(
                return_value=httpx.Response(200, text=valid_arxiv_abstract)
            )

        scraper = HtmlScraper(base_url="https://arxiv.org")

        async with httpx.AsyncClient() as client:
            articles = await scraper.get_details_batch(client, ids)

        assert len(articles) == 3
        assert all(a is not None for a in articles)
        assert all(a.arxiv_id in ids for a in articles)


@pytest.mark.asyncio
async def test_get_details_batch_empty_list():
    """Empty input returns empty list"""
    scraper = HtmlScraper(base_url="https://arxiv.org")

    async with httpx.AsyncClient() as client:
        articles = await scraper.get_details_batch(client, [])

    assert articles == []


@pytest.mark.asyncio
async def test_get_details_batch_partial_error(valid_arxiv_abstract):
    """Partial failures — valid articles still returned, failed ones skipped"""
    with respx.mock(base_url="https://arxiv.org") as respx_mock:
        respx_mock.get("/abs/2603.30045").mock(
            return_value=httpx.Response(200, text=valid_arxiv_abstract)
        )
        respx_mock.get("/abs/2603.30046").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        respx_mock.get("/abs/2603.30047").mock(
            return_value=httpx.Response(200, text=valid_arxiv_abstract)
        )

        scraper = HtmlScraper(base_url="https://arxiv.org")

        async with httpx.AsyncClient() as client:
            articles = await scraper.get_details_batch(
                client, ["2603.30045", "2603.30046", "2603.30047"]
            )

        # failed one skipped, two valid ones returned
        assert len(articles) == 2
        assert all(a is not None for a in articles)


@pytest.mark.asyncio
async def test_get_details_batch_all_errors():
    """All requests fail — returns empty list, does not raise"""
    ids = ["2603.30045", "2603.30046"]

    with respx.mock(base_url="https://arxiv.org") as respx_mock:
        for id in ids:
            respx_mock.get(f"/abs/{id}").mock(
                return_value=httpx.Response(500, text="Internal Server Error")
            )

        scraper = HtmlScraper(base_url="https://arxiv.org")

        async with httpx.AsyncClient() as client:
            articles = await scraper.get_details_batch(client, ids)

        assert articles == []


@pytest.mark.asyncio
async def test_get_details_batch_malformed_mixed(
    valid_arxiv_abstract, invalid_arxiv_abstract
):
    """Mix of valid and malformed HTML — only valid ones returned"""
    with respx.mock(base_url="https://arxiv.org") as respx_mock:
        respx_mock.get("/abs/2603.30045").mock(
            return_value=httpx.Response(200, text=valid_arxiv_abstract)
        )
        respx_mock.get("/abs/2603.30046").mock(
            return_value=httpx.Response(200, text=invalid_arxiv_abstract)
        )

        scraper = HtmlScraper(base_url="https://arxiv.org")

        async with httpx.AsyncClient() as client:
            articles = await scraper.get_details_batch(
                client, ["2603.30045", "2603.30046"]
            )

        assert len(articles) == 1
        assert articles[0].arxiv_id == "2603.30045"