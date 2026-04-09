from sqlmodel import SQLModel, Field
#from pydantic import HttpUrl,List,BaseModel
from datetime import date, datetime,timezone
from typing import Optional
import sqlalchemy as sa

#SQL models for storing article and score
class ArticleBase(SQLModel, table=False):
    arxiv_id: str = Field(unique=True, index=True)
    title: Optional[str]  = Field(default=None,min_length=5)
    abstract: str  = Field(min_length=10)
    summary: Optional[str] = Field(default=None,min_length=5)
    fetched_at: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
        default_factory=lambda:datetime.now(timezone.utc))


class Article(ArticleBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    scraped_at: Optional[datetime] = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True)),
        default=None)
    processed: bool = Field(default=False)

class RelevanceScore(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id")
    auto_score: float
    manual_score: Optional[float] = None
    matched_keywords: str  # JSON list
    scored_at: datetime = Field(default_factory=datetime.now(timezone.utc))




# input validation — what the scraper produces
class ArticleIn(ArticleBase):
    pass
