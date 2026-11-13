from fastapi.testclient import TestClient
from shared import Article,RelevanceScore
from shared.usermodels import UserInDB
from api.main import app
from api.v1.endpoints.articles import get_session_dep
from api.v1.endpoints.auth import create_token
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import timedelta
import random
import json

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """
    Overlays the route dependencies with the isolated test session
    and provides an HTTP client to hit your endpoints.
    """
    # 1. Force FastAPI to use our transactional test session
    app.dependency_overrides[get_session_dep] = lambda: db_session

    # 2. Yield the HTTP client to the test
    async with  AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:#TestClient(app) as c: 
        yield ac

    # 3. Clean up the override after the test finishes so it doesn't leak
    app.dependency_overrides.clear()



@pytest_asyncio.fixture
async def createitem(db_session):

    existing_article = Article(arxiv_id="2603.30040", title="Old Paper", abstract="Some paper content")
    db_session.add(existing_article)
    await db_session.commit()


@pytest_asyncio.fixture
async def validToken(db_session):
    user = UserInDB(username="test",email="abc@gmail.com",hashed_password="accccc",disabled=False)
    db_session.add(user)
    await db_session.commit()
    access_token_expires = timedelta(minutes=1)

    access_token = create_token(
            data={"sub": "abc@gmail.com", "type":"access"}, expires_delta=access_token_expires
        )
    yield access_token
    
@pytest.mark.asyncio
async def test_read_item(createitem,client,validToken):


    response = await client.get("/v1/articles/1", headers={"Authorization": f"Bearer {validToken}"})
    assert response.status_code == 200
    art = response.json()
    assert art["id"] == 1
    assert art["title"] == "Old Paper"
    assert art["abstract"] == "Some paper content"
    assert art["arxiv_id"] == "2603.30040"
    


@pytest.mark.asyncio
async def test_read_item_bad_token(createitem,client):
    response = await client.get("/v1/articles/1", headers={"Authorization": "hailhydra"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_read_nonexistent_item(client,validToken):
    response = await client.get("/v1/articles/1", headers={"Authorization": f"Bearer {validToken}"})
    assert response.status_code == 404
    assert response.json() == {"detail": "article not found"}


@pytest_asyncio.fixture
async def create30articles(db_session):
    keyword_list = [
        "3D Reconstruction",
        "Virtual Try-On",
        "Photogrammetry",
        "Human Parametric Model",
        "multi-view synchronization",
        "3DGS"
        
    ]
    for i in range(30):
        
        arxiv_id = f"2603.300{i}"
        title = f"Oldpaper{i}"
        abstract = f"Big study on big stuff{i}"
        if i<20:
            score = random.uniform(0.5,1)
            matched_keywords = random.sample(keyword_list,2)
            status = "indexed"
        elif i<28:
            score = random.uniform(0.1,0.5)
            matched_keywords = random.sample(keyword_list,1)
            status = "rejected"
        else:
            score = None
            matched_keywords = None
            status = "unknown"

        article = Article(arxiv_id=arxiv_id, title=title, abstract=abstract,processed=True,status=status,keywords=["stuff","study","big"])
        db_session.add(article)
        await db_session.commit()
        await db_session.refresh(article)
        if score is not None and article.id:
            scoreob = RelevanceScore(article_id=article.id,score=score,matched_keywords=json.dumps(matched_keywords))
            db_session.add(scoreob)
            await db_session.commit()


@pytest.mark.asyncio
async def test_read_items(create30articles,client,validToken):


    response = await client.get("/v1/articles", headers={"Authorization": f"Bearer {validToken}"},params={"limit":50, "offset":0})
    assert response.status_code == 200
    art = response.json()
    assert len(art) == 30
    
@pytest.mark.asyncio
async def test_read_items_indexed(create30articles,client,validToken):


    response = await client.get("/v1/articles", headers={"Authorization": f"Bearer {validToken}"},params={"limit":50, "offset":0, "state":"indexed"})
    assert response.status_code == 200
    art = response.json()
    assert len(art) == 20

@pytest.mark.asyncio
async def test_read_items_rejected(create30articles,client,validToken):


    response = await client.get("/v1/articles", headers={"Authorization": f"Bearer {validToken}"},params={"limit":50, "offset":0, "state":"rejected"})
    assert response.status_code == 200
    art = response.json()
    assert len(art) == 8

@pytest.mark.asyncio
async def test_read_items_unknown(create30articles,client,validToken):


    response = await client.get("/v1/articles", headers={"Authorization": f"Bearer {validToken}"},params={"limit":50, "offset":0, "state":"unknown"})
    assert response.status_code == 200
    art = response.json()
    assert len(art) == 2

@pytest.mark.asyncio
async def test_read_items_score_high(create30articles,client,validToken):


    response = await client.get("/v1/articles", headers={"Authorization": f"Bearer {validToken}"},params={"limit":50, "offset":0, "min":0.5,"max":1})
    assert response.status_code == 200
    art = response.json()
    assert len(art) == 20

@pytest.mark.asyncio
async def test_read_items_score_low(create30articles,client,validToken):


    response = await client.get("/v1/articles", headers={"Authorization": f"Bearer {validToken}"},params={"limit":50, "offset":0, "min":0,"max":0.5})
    assert response.status_code == 200
    art = response.json()
    assert len(art) == 8