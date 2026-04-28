from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from shared.config import settings
from contextlib import asynccontextmanager,suppress
from sqlalchemy.exc import ProgrammingError
from sqlmodel import SQLModel
from sqlalchemy import text
import asyncpg



async def create_database():
    # Connect to the default 'postgres' database
    conn = await asyncpg.connect(user=settings.db_user, password=settings.POSTGRES_PASSWORD, 
                                 host=settings.db_host, database='postgres')
    
    try:
        # Use DROP DATABASE with FORCE to terminate other connections (Postgres 13+)
        # If using an older version, remove 'WITH (FORCE)'
        await conn.execute(f'CREATE DATABASE "{settings.POSTGRES_DB}"')
        print(f"Database '{settings.POSTGRES_DB}' created successfully.")
    except Exception as e:
        print(f"Error creating database: {e}")
    finally:
        await conn.close()

async def delete_database():
    # Connect to the default 'postgres' database
    conn = await asyncpg.connect(user=settings.db_user, password=settings.POSTGRES_PASSWORD, 
                                 host=settings.db_host, database='postgres')
    
    try:
        # Use DROP DATABASE with FORCE to terminate other connections (Postgres 13+)
        # If using an older version, remove 'WITH (FORCE)'
        await conn.execute(f'DROP DATABASE "{settings.POSTGRES_DB}" WITH (FORCE)')
        print(f"Database '{settings.POSTGRES_DB}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting database: {e}")
    finally:
        await conn.close()


engine = create_async_engine(settings.database_url)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_tables():
    async with engine.begin() as conn:
        def enable_vector(connection):
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        await conn.run_sync(enable_vector)
        await conn.run_sync(SQLModel.metadata.create_all)

@asynccontextmanager
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session