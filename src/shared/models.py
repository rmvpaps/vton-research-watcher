from sqlmodel import SQLModel, Field, Column, Relationship,String,JSON
#from pydantic import HttpUrl,List,BaseModel
from datetime import date, datetime,timezone
from typing import Optional,List
from enum import Enum
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB


class ArticleState(str, Enum):
    INDEXED = "indexed"
    REJECTED = "rejected"
    UNKNOWN = "unknown"

#SQL models for storing article and score
class ArticleBase(SQLModel, table=False):
    arxiv_id: str = Field(unique=True, index=True)
    title: Optional[str]  = Field(default=None,min_length=5)
    abstract: str  = Field(min_length=10)
    authors: Optional[List[str]]= Field(default=[], sa_type=JSON)
    published_at: Optional[datetime] = Field(
            sa_column=sa.Column(sa.DateTime(timezone=True)),
            default=None)
    source: Optional[str] = Field(default='ARXIV_CS', min_length=5)
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
    #DENORMALIZED FIELDS - These are stored in the Article table for faster filtering and searching.
    keywords: Optional[List[str]]= Field(default=[], sa_type=JSON)




class Enriched(SQLModel,table=False):
    arxiv_id: str 
    title: Optional[str]  = None
    abstract: str
    fetched_at: datetime 
    id: Optional[int] = None
    summary: Optional[str] = None
    chunks: Optional[List[str]] = []
    scraped_at: Optional[datetime] = None
    authors: Optional[List[str]]= []
    published_at: Optional[datetime] = None
    source: Optional[str] = None
        
    processed: bool 
    score: Optional[float] = 0.0
    status: ArticleState = Field(sa_column=String,default=ArticleState.UNKNOWN)
    keywords: Optional[List[str]] = []



class RelevanceScore(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id")
    score: float
    manual_score: Optional[float] = None
    matched_keywords: Optional[str]  = Field(default=None, sa_type=JSONB) # JSON list

    fetched_at: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
        default_factory=lambda:datetime.now(timezone.utc))




class Embedding(SQLModel, table=True):
    # Link it directly to the Article ID
    article_id: int = Field(foreign_key="article.id", primary_key=True)
    chunk_id: int = Field(primary_key=True)
    chunk_text: str = Field(sa_column=Column(sa.Text),min_length=10)
    # 384 dimensions for BGE-Small
    vector: List[float] = Field(sa_column=Column(Vector(384)))


# Note: Storing each keyword as a row is better for 't3.micro' filtering than a JSON list.
class Keyword(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id")
    word: str = Field(index=True) # Index this for fast filtering


class Stats(SQLModel, table=False):
    monthCt: int 
    dayCt:int
    totalRelCt: int
    totalCt: int


class Message(SQLModel, table=False):
    role: str =Field(default=None, primary_key=True)
    content: str =Field(default=None, primary_key=True)


class ArticleChat(SQLModel, table=True):
    last_activity: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
        default_factory=lambda:datetime.now(timezone.utc))
    id: Optional[int] = Field(default=None, primary_key=True)
    message: list["ChatItem"] = Relationship(back_populates="articleChat",cascade_delete=True)
    article_id: int = Field(foreign_key="article.id")

class ChatItem(Message, table=True):
    ts: datetime = Field(
            sa_column=sa.Column(sa.DateTime(timezone=True), primary_key=True),
            default_factory=lambda:datetime.now(timezone.utc))
    chat_id: Optional[int] = Field(foreign_key="articlechat.id")
    articleChat: ArticleChat = Relationship(back_populates="message")


class RangeInt(SQLModel,table=False):
    min: int
    max: int

