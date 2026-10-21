import pytest
from pathlib import Path


@pytest.fixture
def shared_data_dir():
    """Returns the path to the directory containing test data."""
    return Path(__file__).parent / "data"

@pytest.fixture
def valid_arxiv_list(shared_data_dir):
    """Provides the content of a valid ArXiv page."""
    return (shared_data_dir / "list.html").read_text()


@pytest.fixture
def invalid_arxiv_list(shared_data_dir):
    """Provides the content of a valid ArXiv page."""
    return (shared_data_dir / "badlist.html").read_text()


@pytest.fixture
def valid_arxiv_list_bad_paging(shared_data_dir):
    """Provides the content of a valid ArXiv page."""
    return (shared_data_dir / "bad_paging.html").read_text()



@pytest.fixture
def valid_arxiv_abstract(shared_data_dir):
    """Provides the content of a valid ArXiv page."""
    return (shared_data_dir / "valid_abstract.html").read_text()


@pytest.fixture
def valid_arxiv_text(shared_data_dir):
    """Provides the content of a valid ArXiv page."""
    return (shared_data_dir / "valid_text.txt").read_text()

@pytest.fixture
def valid_pdf_data(shared_data_dir):
    """Provides the content of a valid ArXiv page."""
    with open(f"{shared_data_dir}/valid.pdf", "rb") as f:
        return f.read()
    return b""

@pytest.fixture
def invalid_arxiv_abstract(shared_data_dir):
    """Provides the content of a valid ArXiv page."""
    return (shared_data_dir / "bad_abstract.html").read_text()

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlalchemy.orm import sessionmaker
import pytest_asyncio

# conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Import your configuration/methods from database.py
from shared.database import create_database, delete_database, settings
from shared.models import SQLModel  # Crucial: Ensure SQLModel registers your tables

TEST_DB_NAME = "test_db"
# Swap out the DB name in your standard connection string format
TEST_DATABASE_URL = f"postgresql+asyncpg://{settings.db_user}:{settings.POSTGRES_PASSWORD}@{settings.db_host}/{TEST_DB_NAME}"

@pytest_asyncio.fixture(scope="function", autouse=True)
async def manage_test_db():
    """Runs once for the for each test instead of entire test session. Safely builds and drops test_db."""
    # 1. Create the database and run extensions using your file's logic
    await create_database(db_name=TEST_DB_NAME)
    
    # 2. Build the engine targeting the test db and create tables
    test_engine = create_async_engine(TEST_DATABASE_URL)
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        
    yield
    
    # 3. Clean up when all tests finish
    await test_engine.dispose()
    await delete_database(db_name=TEST_DB_NAME)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provides an isolated transaction session for an individual test."""
    test_engine = create_async_engine(TEST_DATABASE_URL)

    asyncSession = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with asyncSession() as session:
        yield session
        
            


# @pytest_asyncio.fixture
# async def db_session():
#     # 1. Create a fresh in-memory DB for every test
#     engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
#     # 2. Create tables
#     async with engine.begin() as conn:
#         await conn.run_sync(SQLModel.metadata.create_all)
    
#     # 3. Yield a session
#     async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
#     async with async_session() as session:
#         yield session
    
#     # 4. Clean up
#     await engine.dispose()




# tests/conftest.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.fixture
def mock_session():
    """A fake AsyncSession with all methods mocked"""
    session = MagicMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.exec = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_get_session(mock_session):
    """
    Replaces get_session context manager with one that
    yields the mock session
    """
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _mock_get_session():
        yield mock_session

    with patch("shared.database.get_session", _mock_get_session):
        yield mock_session

