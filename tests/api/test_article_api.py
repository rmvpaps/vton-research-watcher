from fastapi.testclient import TestClient
from shared import Article
from shared.usermodels import UserInDB
from api.main import app
from api.v1.endpoints.articles import get_session_dep
from api.v1.endpoints.auth import create_token
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import timedelta



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
    


# def test_read_item_bad_token(db_session):
#     response = client.get("/v1/articles", headers={"X-Token": "hailhydra"})
#     assert response.status_code == 400
#     assert response.json() == {"detail": "Invalid X-Token header"}


# def test_read_nonexistent_item(db_session):
#     response = client.get("/v1/articles?ids=800", headers={"X-Token": "coneofsilence"})
#     assert response.status_code == 404
#     assert response.json() == {"detail": "Item not found"}

