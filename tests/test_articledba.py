# tests/test_db_interactions.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from shared.models import Article
from shared import article_dba  # adjust import to your structure


# ── save_article ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_article_success(mock_get_session):
    """Article is added, committed and refreshed"""
    article = Article(
        arxiv_id="2603.30045",
        title="A Vision Transformer",
        abstract="We propose a novel approach to object detection.",
        fetched_at=datetime.now(timezone.utc),
    )

    async with mock_get_session() as mock_session:
        result = await article_dba.store_results(mock_session, article)

        mock_session.add.assert_called_once_with(article)
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(article)
        assert result == article


@pytest.mark.asyncio
async def test_save_article_commit_fails(mock_get_session, mock_session):
    """Returns None gracefully when commit raises"""
    mock_session.commit.side_effect = Exception("DB connection lost")

    article = Article(
        arxiv_id="2603.30045",
        title="A Vision Transformer",
        abstract="We propose a novel approach to object detection.",
        fetched_at=datetime.now(timezone.utc),
    )

    with mock_get_session() as session:
        result = await article_dba.store_results(session, article)
        assert result is None
        session.add.assert_called_once_with(article)


# ── remove_duplicates ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remove_duplicates_all_new(db_session):
    """No existing IDs in DB — all returned as new"""
    existing_article = Article(arxiv_id="2603.30040", title="Old Paper", abstract="Some paper content")
    db_session.add(existing_article)
    await db_session.commit()
    ids = ["2603.30045", "2603.30046", "2603.30047"]

    new_ids = await article_dba.removeDuplicates(db_session, ids)

    assert new_ids == ids
    


@pytest.mark.asyncio
async def test_remove_duplicates_some_exist(db_session):
    """Some IDs already in DB — only new ones returned"""
    existing_article = Article(arxiv_id="2603.30045", title="Old Paper", abstract="Some paper content")
    db_session.add(existing_article)
    await db_session.commit()
    
    ids = ["2603.30045", "2603.30046", "2603.30047"]
    new_ids = await article_dba.removeDuplicates(db_session, ids)

    assert new_ids == ["2603.30046", "2603.30047"]
    assert "2603.30045" not in new_ids


@pytest.mark.asyncio
async def test_remove_duplicates_all_exist(db_session):
    """All IDs already in DB — empty list returned"""
    existing_article = Article(arxiv_id="2603.30045", title="Old Paper", abstract="Some paper content")
    db_session.add(existing_article)
    await db_session.commit()
    existing_article = Article(arxiv_id="2603.30046", title="Old Paper", abstract="Some paper content")
    db_session.add(existing_article)
    await db_session.commit()
    
    ids = ["2603.30045", "2603.30046"]
    new_ids = await article_dba.removeDuplicates(db_session, ids)

    assert new_ids == []


@pytest.mark.asyncio
async def test_remove_duplicates_empty_input(db_session):
    """Empty input — no DB call needed, returns empty"""
    ids = []
    
    new_ids = await article_dba.removeDuplicates(db_session, ids)

    assert new_ids == []
    

@pytest.mark.asyncio
async def test_remove_duplicates_db_error(mock_get_session, mock_session):
    """DB error — returns empty list, does not raise"""
    mock_session.exec.side_effect = Exception("Connection refused")

    ids = ["2603.30045", "2603.30046"]
    async with mock_get_session() as session:
        new_ids = await article_dba.removeDuplicates(session, ids)

        assert new_ids == []

