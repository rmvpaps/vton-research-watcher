
from typing import Annotated
from shared import get_session_dep,Article,settings,RelevanceScore
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
import asyncio

SessionDep = Annotated[Session, Depends(get_session_dep)]
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    print(f"Registered tables: {SQLModel.metadata.tables.keys()}")
    print(settings.database_url)

@app.get("/articles/")
async def read_articles(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    score:bool = False
) -> list[Article]:
    """Returns all articles in the system"""

    if not score:
        result = await session.exec(select(Article).offset(offset).limit(limit))
        articles = result.all()
        return articles

    else:
        statement = select(Article).join(RelevanceScore, Article.id==RelevanceScore.article_id).order_by(RelevanceScore.score)
        result = await session.exec(statement)
        articles = result.all()
        return articles