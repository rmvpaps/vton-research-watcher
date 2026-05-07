import pytest
import respx
import httpx

from scraper.htmlScraper import HtmlScraper,HtmlStructureException
 

@pytest.mark.asyncio
async def test_extract_info_from_listing_success(valid_arxiv_list):
        scraper = HtmlScraper(base_url="https://arxiv.org")
        ids,total = scraper.extract_info_from_listing(valid_arxiv_list)



        assert len(ids) == 25
        assert ids[0] == "2603.30045"
        assert total == 75


@pytest.mark.asyncio
async def test_extract_info_from_listing_nostruct():
        scraper = HtmlScraper(base_url="https://arxiv.org")
     
        fake_html = "text"
        with pytest.raises(HtmlStructureException) as e_info:
                ids,total = scraper.extract_info_from_listing(fake_html)
        



@pytest.mark.asyncio
async def test_extract_info_from_listing_incorrect_struct():
        scraper = HtmlScraper(base_url="https://arxiv.org")
     
        fake_html = "<html><a title='Abstract' href='/abs/2401.12345'>...</a>"+ \
        "<div class='paging'>Total of 75 entries :      <span>1-25</span>" + \
        "<a href=/list/cs.CV/pastweek?skip=25&amp;show=25>26-50</a><span>...</span>" + \
        "<a href=/list/cs.CV/pastweek?skip=900&amp;show=25>51-75</a>" + \
        "</div></html>"
        with pytest.raises(HtmlStructureException) as e_info:
                ids,total = scraper.extract_info_from_listing(fake_html)
                print(ids,total)

        
@pytest.mark.asyncio
async def test_extract_info_from_listing_incorrect_abstractid_format():
        scraper = HtmlScraper(base_url="https://arxiv.org")
     
        fake_html = "<html><dl><dt><a title='Abstract' val='/abstract/2401.12345'>...</a></dt></dl>"+ \
        "<div class='paging'>Total of 75 entries :      <span>1-25</span>" + \
        "<a href=/list/cs.CV/pastweek?skip=25&amp;show=25>26-50</a><span>...</span>" + \
        "<a href=/list/cs.CV/pastweek?skip=900&amp;show=25>51-75</a>" + \
        "</div></html>"
        with pytest.raises(HtmlStructureException) as e_info:
                ids,total = scraper.extract_info_from_listing(fake_html)
                print(ids,total)


@pytest.mark.asyncio
async def test_extract_summary_title():
        scraper = HtmlScraper(base_url="https://arxiv.org")
     
        fake_html = "<html><div id='abs'><h1><span>Title:</span>SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization</h1>" + \
        "<blockquote><span class='descriptor'>Abstract:</span>We present SyncFix, a framework that enforces cross-view consistency during the diffusion-based refinement</blockquote></html>"
        summary,title = scraper.extract_summary_title(fake_html)
        assert summary == "We present SyncFix, a framework that enforces cross-view consistency during the diffusion-based refinement"
        assert title == "SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization"






@pytest.mark.asyncio
async def test_extract_summary_title_valid(valid_arxiv_abstract):
        scraper = HtmlScraper(base_url="https://arxiv.org")
        summary,title = scraper.extract_summary_title(valid_arxiv_abstract)



        assert summary == "We present SyncFix, a framework that enforces cross-view consistency during the diffusion-based refinement of reconstructed scenes. SyncFix formulates refinement as a joint latent bridge matching problem, synchronizing distorted and clean representations across multiple views to fix the semantic and geometric inconsistencies. This means SyncFix learns a joint conditional over multiple views to enforce consistency throughout the denoising trajectory. Our training is done only on image pairs, but it generalizes naturally to an arbitrary number of views during inference. Moreover, reconstruction quality improves with additional views, with diminishing returns at higher view counts. Qualitative and quantitative results demonstrate that SyncFix consistently generates high-quality reconstructions and surpasses current state-of-the-art baselines, even in the absence of clean reference images. SyncFix achieves even higher fidelity when sparse references are available."
        assert title == "SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization"


@pytest.mark.asyncio
async def test_extract_summary_nostruct():
        scraper = HtmlScraper(base_url="https://arxiv.org")
     
        fake_html = "text"
        with pytest.raises(HtmlStructureException) as e_info:
                summary,title = scraper.extract_summary_title(fake_html)
        



@pytest.mark.asyncio
async def test_extract_summarytitle_incorrect_struct():
        scraper = HtmlScraper(base_url="https://arxiv.org")
     
        fake_html = "<html><h1><span>Title:</span>SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization</h1>"+ \
                      "<html><div id='abs'><h1><span>Title:</span>SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization</h1></html>"
        with pytest.raises(HtmlStructureException) as e_info:
                _,_ = scraper.extract_summary_title(fake_html)
                

        
@pytest.mark.asyncio
async def test_extract_summarytitle_incorrect_abstract_format():
        scraper = HtmlScraper(base_url="https://arxiv.org")
     
        fake_html = "<html><dl><dt><a title='Abstract' val='/abstract/2401.12345'>...</a></dt></dl>"+ \
        "<div class='paging'>Total of 75 entries :      <span>1-25</span>" + \
        "<a href=/list/cs.CV/pastweek?skip=25&amp;show=25>26-50</a><span>...</span>" + \
        "<a href=/list/cs.CV/pastweek?skip=900&amp;show=25>51-75</a>" + \
        "</div></html>"
        with pytest.raises(HtmlStructureException) as e_info:
                ids,total = scraper.extract_info_from_listing(fake_html)
                print(ids,total)


@pytest.mark.asyncio
async def test_extract_summary_title_no_title():
        scraper = HtmlScraper(base_url="https://arxiv.org")
     
        fake_html = "<html><div id='abs'>" + \
        "<blockquote><span class='descriptor'>Abstract:</span>We present SyncFix, a framework that enforces cross-view consistency during the diffusion-based refinement</blockquote></html>"
        with pytest.raises(HtmlStructureException) as e_info:
        
                summary,title = scraper.extract_info_from_listing(fake_html)
        

