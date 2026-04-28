from sqlmodel import SQLModel, Field, Column, Relationship
#from pydantic import HttpUrl,List,BaseModel
from datetime import date, datetime,timezone
from typing import Optional,List
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

#SQL models for storing article and score
class ArticleBase(SQLModel, table=False):
    arxiv_id: str = Field(unique=True, index=True)
    title: Optional[str]  = Field(default=None,min_length=5)
    abstract: str  = Field(min_length=10)
    fetched_at: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
        default_factory=lambda:datetime.now(timezone.utc))


class Article(ArticleBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    summary: Optional[str] = Field(default=None,min_length=5)
    scraped_at: Optional[datetime] = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True)),
        default=None)
    processed: bool = Field(default=False)
    status: str = Field(default="unknown")

    # # Relationships (Allows you to access data via article.embedding or article.keywords)
    # embedding: Optional["BGEEmbedding"] = Relationship(back_populates="article")
    # keywords: List["Keyword"] = Relationship(back_populates="article")


class Enriched(SQLModel,table=False):
    arxiv_id: str 
    title: Optional[str]  = None
    abstract: str
    fetched_at: datetime 
    id: Optional[int] = None
    summary: Optional[str] = None
    scraped_at: Optional[datetime] = None
    processed: bool 
    status: str 
    embedding: Optional[List[float]] = []
    keywords: Optional[List[str]] = []

class RelevanceScore(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id")
    score: float
    manual_score: Optional[float] = None
    matched_keywords: Optional[str]  # JSON list

    fetched_at: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
        default_factory=lambda:datetime.now(timezone.utc))




class BGEEmbedding(SQLModel, table=True):
    # Link it directly to the Article ID
    article_id: int = Field(foreign_key="article.id", primary_key=True)
    
    # 384 dimensions for BGE-Small
    vector: List[float] = Field(sa_column=Column(Vector(384)))


# Note: Storing each keyword as a row is better for 't3.micro' filtering than a JSON list.
class Keyword(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id")
    word: str = Field(index=True) # Index this for fast filtering

