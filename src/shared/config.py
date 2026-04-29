from pydantic_settings import BaseSettings
from pydantic import computed_field
from typing import Optional

class Settings(BaseSettings):
    scraper_mode: str = "html"
    processor_mode: str = "transformer"
    llm_host:str=''
    llm_api_key:str=''
    baseURL:str = "https://arxiv.org/list/cs.CV/pastweek"
    scrape_concurrency:int = 1
    ARXIV_ABS_URL:str = "https://arxiv.org/abs/"
    ARXIV_PDF_URL:str = "https://arxiv.org/pdf/"
    db_type: Optional[str] = "sqlite"
    POSTGRES_PASSWORD: str = "default123"
    POSTGRES_DB: str = "vton_research"
    db_protocol: str = "postgresql+asyncpg"
    db_user:str = "postgres"
    db_host:str = "localhost"
    redis_url: str = "redis://localhost:6379"
    keywords_path: str = "keywords.yaml"
    scrape_concurrency: int = 2
    scrape_window_rate_min: int = 10
    scrape_delay_seconds: float = 5.0
    dummy:bool = True
    summarizer_path:str = "C:/Users/Lenovo/.cache/huggingface/hub/models--t5-small/snapshots/df1b051c49625cf57a3d0d8d3863ed4d13564fe4"
    embedding_path:str = "C:/Users/Lenovo/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5/snapshots/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
    keybert_path:str = "C:/Users/Lenovo/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf"

    @computed_field
    @property
    def database_url(self) -> str:
        if self.db_type == "sqlite":
            return "sqlite+aiosqlite:///database.db"
        return f"{self.db_protocol}://{self.db_user}:{self.POSTGRES_PASSWORD}@{self.db_host}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"

settings = Settings()