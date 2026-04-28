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

@pytest_asyncio.fixture
async def db_session():
    # 1. Create a fresh in-memory DB for every test
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # 2. Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # 3. Yield a session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    # 4. Clean up
    await engine.dispose()


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