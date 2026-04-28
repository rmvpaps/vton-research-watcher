import pytest
import respx
import httpx

from processor.simple_processor import simpleTransformerProcessor
from shared import Article 

@pytest.mark.asyncio
async def test_evaluate_score_match():
        keywords = ["natural language processing","information retrieval","similarity"]
        art1 = Article(arxiv_id="2001.2001",title="lorem ipsum dolorem",abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.")
        processor = simpleTransformerProcessor(keywords=keywords)
        score = await processor.evaluate_abstract(art1)

        assert score is not None
        assert score.score > 0 and score.score < 1
        assert score.score > 0.7
        assert score.matched_keywords == '["natural language processing", "information retrieval", "similarity"]'

@pytest.mark.asyncio
async def test_evaluate_score_nomatch():
        keywords = ["funny","sorry","ding-dong-bell"]
        art1 = Article(arxiv_id="2001.2001",title="lorem ipsum dolorem",abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.")
        processor = simpleTransformerProcessor(keywords=keywords)
        score = await processor.evaluate_abstract(art1)

        assert score is not None
        assert score.score > 0 and score.score < 1
        assert score.score < 0.3
        assert score.matched_keywords == '[]'


@pytest.mark.asyncio
async def test_evaluate_score_partial_match():
        keywords = ["information retrieval","fan","propeller"]
        art1 = Article(arxiv_id="2001.2001",title="lorem ipsum dolorem",abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.")
        processor = simpleTransformerProcessor(keywords=keywords)
        score = await processor.evaluate_abstract(art1)

        assert score is not None
        assert score.score > 0 and score.score < 1
        assert score.score < 0.7
        assert score.score > 0.3
        assert score.matched_keywords == '["information retrieval"]'


@pytest.mark.asyncio
async def test_generate_summary_small():
    # Setup
    keywords = ["3d reconstruction"]
    processor = simpleTransformerProcessor(keywords=keywords)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", arxiv_id="123")
    sample_text = """We present SyncFix, a framework that enforces cross-view consistency during the diffusion-based refinement of reconstructed scenes. SyncFix formulates refinement as a joint latent bridge matching problem, synchronizing distorted and clean representations across multiple views to fix the semantic and geometric inconsistencies. This means SyncFix learns a joint conditional over multiple views to enforce consistency throughout the denoising trajectory. Our training is done only on image pairs, but it generalizes naturally to an arbitrary number of views during inference. Moreover, reconstruction quality improves with additional views, with diminishing returns at higher view counts. Qualitative and quantitative results demonstrate that SyncFix consistently generates high-quality reconstructions and surpasses current state-of-the-art baselines, even in the absence of clean reference images. SyncFix achieves even higher fidelity when sparse references are available."""

    # Action
    summary = await processor.generateSummary(art, sample_text)

    # Assertions
    assert isinstance(summary, str)
    assert len(summary) > 0
    
    wordcount = len(summary.split())
    assert wordcount > 20
    assert wordcount < len(sample_text.split())/2


@pytest.mark.asyncio
async def test_generate_summary_big(valid_arxiv_text):
    """ Test if chunking works and summary is less than half in wordcount"""
    # Setup
    keywords = ["3d reconstruction"]
    processor = simpleTransformerProcessor(keywords=keywords)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", arxiv_id="123")
    sample_text = valid_arxiv_text
    

    # Action
    summary = await processor.generateSummary(art, sample_text)

    # Assertions
    assert isinstance(summary, str)
    assert len(summary) > 0
    
    wordcount = len(summary.split())
    assert wordcount > 20
    assert wordcount < len(sample_text.split())/2

@pytest.mark.asyncio
async def test_generate_keywords(valid_arxiv_text):
    # Setup
    keywords = ["3d reconstruction"]
    processor = simpleTransformerProcessor(keywords=keywords)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", arxiv_id="123")
    sample_text = valid_arxiv_text

     # Action
    keywords = await processor.generateKeywords(art, sample_text)

    # Assertions
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    
    expected_keywords = ['multiview', 'reconstruction', 'syncfix', 'benchmarking','denoising']
    for i in expected_keywords:
        assert i in keywords


@pytest.mark.asyncio
async def test_generate_keywords(valid_arxiv_text):
    # Setup
    keywords = ["3d reconstruction"]
    processor = simpleTransformerProcessor(keywords=keywords)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", arxiv_id="123")
    sample_text = valid_arxiv_text

     # Action
    keywords = await processor.generateKeywords(art, sample_text)

    # Assertions
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    
    expected_keywords = ['multiview', 'reconstruction', 'syncfix', 'benchmarking','denoising']
    for i in expected_keywords:
        assert i in keywords



from datetime import datetime,timezone
@pytest.mark.asyncio
async def test_evaluate_text(valid_arxiv_text):
    # Setup
    keywords = ["3d reconstruction"]
    processor = simpleTransformerProcessor(keywords=keywords)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", 
                  abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", 
                  arxiv_id="123",
                  fetched_at=datetime.now(timezone.utc),
                  processed=False,
                  status="unknown")
    sample_text = valid_arxiv_text

     # Action
    new_article = await processor.evaluate_text(art, sample_text)

    # Assertions
    assert new_article.summary is not None
    assert new_article.keywords is not None
    assert len(new_article.keywords)>0
    assert new_article.embedding is not None
    assert len(new_article.embedding) > 0

    expected_keywords = ['multiview', 'reconstruction', 'syncfix', 'benchmarking','denoising']
    for i in expected_keywords:
        assert i in new_article.keywords



