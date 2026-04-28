import pytest
import respx
import httpx


from unittest.mock import AsyncMock, MagicMock, patch

import os

os.environ['TRANSFORMERS_OFFLINE'] = '1'

from processor.processing_service import ProcessingService
from processor import simpleFullTextExtractor,processing_service
from shared import Article,Enriched,article_dba
from datetime import datetime,timezone



# @pytest.mark.asyncio
# async def test_download_get_text_from_validpdfurl(valid_pdf_data):
    
#     # 1. Setup the Mock Server using respx
#     with respx.mock(base_url="https://arxiv.org") as respx_mock:

        

#         respx_mock.get("/pdf/1001.2001").mock(
#             return_value=httpx.Response(status_code=200, content=valid_pdf_data)
#         )


#         # 2. Instantiate your actual scraper
#         extractor = simpleFullTextExtractor()
    
#         # 3. Use a real AsyncClient (it will be intercepted by respx)
#         text = await extractor.download_get_text("1001.2001")

#         # 4. Assertions
#         assert isinstance(text,str)
#         assert len(text) > 5000
#         assert text == ""


@pytest.mark.asyncio
async def test_processing_service_notrelevant(mock_session,mock_get_session,mocker):
    # Create an async mock that returns a custom value
    mock_update = AsyncMock(return_value=None)

    #mock article dba updatearticle function
    with patch("processor.processing_service.updateArticle", mock_update):
        


        # 2. Instantiate service
        service = ProcessingService()

        #assuming article fetched from DB
        art = Article(title="Cosine similarity", 
                abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", 
                arxiv_id="1001.2001",
                fetched_at=datetime.now(timezone.utc),
                processed=False,
                status="unknown")
        async with mock_get_session() as mock_session:
            res = await service.process_article(mock_session,art)

            art.processed = True
            art.status = 'rejected'
            #assert mockupdate called with argument processed true, status indexed
            mock_update.assert_awaited_once_with(mock_session,art)





@pytest.mark.asyncio
async def test_processing_service_relevant(valid_pdf_data,mock_session,mock_get_session,mocker):
    # Create an async mock that returns a custom value
    mock_update = AsyncMock(return_value=None)

    #mock article dba updatearticle function
    with patch("processor.processing_service.updateArticle", mock_update):
        # 1. Setup the Mock Server using respx
        with respx.mock(base_url="https://arxiv.org") as respx_mock:

            respx_mock.get("/pdf/1001.2001").mock(
                return_value=httpx.Response(status_code=200, content=valid_pdf_data)
            )


            # 2. Instantiate service
            service = ProcessingService()

            #assuming article fetched from DB
            art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", 
                    abstract="We present SyncFix, a framework that enforces cross-view consistency during the diffusion-based refinement of reconstructed scenes. SyncFix formulates refinement as a joint latent bridge matching problem, synchronizing distorted and clean representations across multiple views to fix the semantic and geometric inconsistencies. This means SyncFix learns a joint conditional over multiple views to enforce consistency throughout the denoising trajectory. Our training is done only on image pairs, but it generalizes naturally to an arbitrary number of views during inference. Moreover, reconstruction quality improves with additional views, with diminishing returns at higher view counts. Qualitative and quantitative results demonstrate that SyncFix consistently generates high-quality reconstructions and surpasses current state-of-the-art baselines, even in the absence of clean reference images. SyncFix achieves even higher fidelity when sparse references are available.", 
                    arxiv_id="1001.2001",
                    fetched_at=datetime.now(timezone.utc),
                    processed=False,
                    status="unknown")
            async with mock_get_session() as mock_session:
                res = await service.process_article(mock_session,art)

                art.processed = True
                art.status = 'indexed'
                #assert mockupdate called with argument processed true, status indexed
                mock_update.assert_awaited_once_with(mock_session,art)
                
