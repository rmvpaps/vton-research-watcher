import pytest
import respx
import httpx

from processor.simple_processor import simpleTransformerProcessor
from shared import Article ,ArticleState
from .fixtures import processutil

@pytest.mark.asyncio
async def test_evaluate_score_match(processutil):
        keywords = ["natural language processing","information retrieval","similarity"]
        art1 = Article(arxiv_id="2001.2001",title="lorem ipsum dolorem",abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.")
        processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
        score = await processor.evaluate_abstract(art1)

        assert score is not None
        assert score.score > 0 and score.score < 1
        assert score.score > 0.7
        assert score.matched_keywords == '["natural language processing", "information retrieval", "similarity"]'

@pytest.mark.asyncio
async def test_evaluate_score_nomatch(processutil):
        keywords = ["funny","sorry","ding-dong-bell"]
        art1 = Article(arxiv_id="2001.2001",title="lorem ipsum dolorem",abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.")
        processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
        score = await processor.evaluate_abstract(art1)

        assert score is not None
        assert score.score > 0 and score.score < 1
        assert score.score < 0.5
        assert score.matched_keywords == '[]'


@pytest.mark.asyncio
async def test_evaluate_score_partial_match(processutil):
        keywords = ["information retrieval","air circulation","ranking","propeller"]
        art1 = Article(arxiv_id="2001.2001",title="lorem ipsum dolorem",abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.")
        processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
        score = await processor.evaluate_abstract(art1)

        assert score is not None
        assert score.score > 0 and score.score < 1
        assert score.score < 0.7
        assert score.score > 0.5
        assert score.matched_keywords == '["information retrieval"]'
        


@pytest.mark.asyncio
async def test_generate_summary_small(processutil):
    # Setup
    keywords = ["3d reconstruction", "virtual try on","photogrammetry"]
    processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
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
async def test_generate_chunks_small(processutil):
    # Setup
    keywords = ["3d reconstruction", "virtual try on","photogrammetry"]
    processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", arxiv_id="123")
    sample_text = """We present SyncFix, a framework that enforces cross-view consistency during the diffusion-based refinement of reconstructed scenes. 
    SyncFix formulates refinement as a joint latent bridge matching problem, synchronizing distorted and clean representations across multiple views to fix the semantic and geometric inconsistencies. 
    This means SyncFix learns a joint conditional over multiple views to enforce consistency throughout the denoising trajectory. Our training is done only on image pairs, but it generalizes naturally 
    to an arbitrary number of views during inference. Moreover, reconstruction quality improves with additional views, with diminishing returns at higher view counts. Qualitative and quantitative results 
    demonstrate that SyncFix consistently generates high-quality reconstructions and surpasses current state-of-the-art baselines, even in the absence of clean reference images. SyncFix achieves 
    even higher fidelity when sparse references are available."""

    # Action
    chunks = await processor.generateChunks(art, sample_text)

    # Assertions
    assert len(chunks) > 0
    assert isinstance(chunks[0], str)
    print(chunks)
    wordcount = len(chunks[0].split())
    assert wordcount > 20
    assert wordcount < len(sample_text.split())/2




@pytest.mark.asyncio
async def test_generate_summary_big(valid_arxiv_text,processutil):
    """ Test if chunking works and summary is less than half in wordcount"""
    # Setup
    keywords = ["3d reconstruction", "virtual try on","photogrammetry"]
    processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
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
async def test_generate_chunks_big(valid_arxiv_text, processutil):
    # Setup
    keywords = ["3d reconstruction", "virtual try on","photogrammetry"]
    processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", arxiv_id="123")
    
    # Action
    chunks = await processor.generateChunks(art, valid_arxiv_text)

    min_chunks_expected = int(len(valid_arxiv_text.split())/512)
    # Assertions
    assert len(chunks) > min_chunks_expected
    assert isinstance(chunks[0], str)
    print(chunks)
    wordcount = len(chunks[0].split())
    assert wordcount > 200
    assert wordcount < 512



@pytest.mark.asyncio
async def test_create_embeddings(processutil):
    chunks = [ "SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization - This paper presents a novel method for 3d reconstruction from sparse representations",
               "Part of paper discussing SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization. \n SyncFix enforces cross-view consistency during the diffusion-based refinement of distill the refined outputs back into the 3D representation.",
               "Part of paper discussing SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization. \n independent refinement can produce inconsistent results for ambiguous structures or regions with large artifact  \n\n However, these refinement methods treat each view as an independent 2D generation task. This ignores important cross-view geometric and semantic constraints and that all views are projections of the same underlying 3D scene. Therefore, independent refinement can produce inconsistent results for ambiguous structures or regions with large artifacts across different viewpoints. When these conflicting signals are distilled back into the 3D model, optimization becomes unstable, leading to appearance drift and degraded geometry.\n\nIn this paper, we impose multi-view consistency directly during the refinement process rather than correcting it post hoc. To this end, we introduce SyncFix, a latent bridge matching formulation that models refinement as joint conditional generation over multiple views. SyncFix aligns latent representations across views during the denoising process and encourages information exchange via cross-view attention without any explicit camera information.",
                "Part of paper discussing SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization. \n the views and conclusions contained herein should not be interpreted as necessarily representing the official policies or  \n\n Acknowledgement\nThis research is based upon work supported by the Office of the Director of National Intelligence (ODNI), Intelligence Advanced Research Projects Activity (IARPA), via IARPA R&D Contract No. 140D0423C0076."
            ]
    keywords = ["3d reconstruction", "virtual try on","photogrammetry"]
        
    processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", arxiv_id="123")
        
    # Action
    embeddings = await processor.createEmbeddings(chunks)
    assert len(embeddings) == len(chunks)
    assert len(embeddings[0]) == 384


@pytest.mark.asyncio
async def test_create_embeddings_empty(processutil):
    chunks = [ ]
    keywords = ["3d reconstruction", "virtual try on","photogrammetry"]
        
    processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", arxiv_id="123")
        
    # Action
    embeddings = await processor.createEmbeddings(chunks)
    assert len(embeddings) == len(chunks)
    
    
@pytest.mark.asyncio
async def test_generate_keywords(valid_arxiv_text,processutil):
    # Setup
    keywords = ["3d reconstruction", "virtual try on","photogrammetry"]
    processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", arxiv_id="123")
    sample_text = valid_arxiv_text

     # Action
    keywords = await processor.generateKeywords(art, sample_text)

    # Assertions
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    
    expected_keywords = ['reconstruction', 'syncfix','denoising','3d','consistency']
    for i in expected_keywords:
        assert i in keywords


@pytest.mark.asyncio
async def test_generate_keywords(valid_arxiv_text,processutil):
    # Setup
    keywords = ["3d reconstruction", "virtual try on","photogrammetry"]
    processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", arxiv_id="123")
    sample_text = valid_arxiv_text

     # Action
    keywords = await processor.generateKeywords(art, sample_text)

    # Assertions
    assert isinstance(keywords, set)
    assert len(keywords) > 0
    
    #expected_keywords = ['multiview', 'reconstruction', 'syncfix', 'benchmarking','denoising']
    expected_keywords = ['reconstruction', 'syncfix','denoising','3d','consistency']
        
    for i in expected_keywords:
        assert i in keywords



from datetime import datetime,timezone
@pytest.mark.asyncio
async def test_evaluate_text(valid_arxiv_text,processutil):
    # Setup
    keywords = ["3d reconstruction", "virtual try on","photogrammetry"]
    processor = simpleTransformerProcessor(keywords=keywords,encoding_model=processutil)
    art = Article(title="SyncFix: Fixing 3D Reconstructions via Multi-View Synchronization", 
                  abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", 
                  arxiv_id="123",
                  fetched_at=datetime.now(timezone.utc),
                  processed=False,
                  status=ArticleState.UNKNOWN)
    sample_text = valid_arxiv_text

     # Action
    new_article = await processor.evaluate_text(art, 0.6,sample_text)

    # Assertions
    assert new_article.summary is not None
    assert new_article.keywords is not None
    assert len(new_article.keywords)>0
    #assert new_article.embedding is not None
    #assert len(new_article.embedding) > 0
    #expected_keywords = ['multiview', 'reconstruction', 'syncfix', 'benchmarking','denoising']
    print(new_article.keywords)
    expected_keywords = ['reconstruction', 'syncfix','denoising','3d','consistency']
    for i in expected_keywords:
        assert i.lower() in new_article.keywords



