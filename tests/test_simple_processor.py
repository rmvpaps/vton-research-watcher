import pytest
import respx
import httpx

from processor.simple_processor import simpleTransformerProcessor
from shared import Article 

# @pytest.mark.asyncio
# async def test_evaluate_score_match():
#         keywords = ["natural language processing","information retrieval","similarity"]
#         art1 = Article(arxiv_id="2001.2001",title="lorem ipsum dolorem",abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.")
#         processor = simpleTransformerProcessor(keywords=keywords)
#         score = await processor.evaluate_abstract(art1)

#         assert score is not None
#         assert score.score > 0 and score.score < 1
#         assert score.score > 0.7
#         assert score.matched_keywords == '["natural language processing", "information retrieval", "similarity"]'

# @pytest.mark.asyncio
# async def test_evaluate_score_nomatch():
#         keywords = ["funny","sorry","ding-dong-bell"]
#         art1 = Article(arxiv_id="2001.2001",title="lorem ipsum dolorem",abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.")
#         processor = simpleTransformerProcessor(keywords=keywords)
#         score = await processor.evaluate_abstract(art1)

#         assert score is not None
#         assert score.score > 0 and score.score < 1
#         assert score.score < 0.3
#         assert score.matched_keywords == '[]'


# @pytest.mark.asyncio
# async def test_evaluate_score_partial_match():
#         keywords = ["information retrieval","fan","propeller"]
#         art1 = Article(arxiv_id="2001.2001",title="lorem ipsum dolorem",abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.")
#         processor = simpleTransformerProcessor(keywords=keywords)
#         score = await processor.evaluate_abstract(art1)

#         assert score is not None
#         assert score.score > 0 and score.score < 1
#         assert score.score < 0.7
#         assert score.score > 0.3
#         assert score.matched_keywords == '["information retrieval"]'


@pytest.mark.asyncio
async def test_generate_summary():
    # Setup
    keywords = ["3d reconstruction"]
    processor = simpleTransformerProcessor(keywords=keywords)
    art = Article(title="Similarity using cosine", abstract="Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it.", arxiv_id="123")
    sample_text = "Cosine similarity proved useful in many different areas, such as in machine learning applications, natural language processing, and information retrieval. After reading this article, you will know precisely what cosine similarity is, how to run it with Python using the scikit-learn library (also known as sklearn), and when to use it. You’ll also learn how cosine similarity is related to graph databases, exploring the quickest way to utilize it."

    # Action
    summary = await processor.generateSummary(art, sample_text)

    # Assertions
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert summary =="Cosine similarity"
