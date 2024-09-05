import enum
import os

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class profiletype(enum.Enum):
    Candidate = "Candidate"
    Talent = "Talent"


async def get_database_session():
    engine = await asyncio.to_thread(create_async_engine, os.getenv('DATABASE_URI_asyncpg'))
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    session = SessionLocal()
    return session


async def setup_database():
    DATABASE_URI = os.getenv('DATABASE_URI')
    if DATABASE_URI is None:
        logger.warning("No DATABASE_URI")
        raise ValueError("No DATABASE_URI set for the database. Set the DATABASE_URI environment variable.")

    engine = await asyncio.to_thread(create_engine, DATABASE_URI)
    SessionLocal = sessionmaker(bind=engine)
    Base = await asyncio.to_thread(declarative_base)

    return engine, SessionLocal, Base


async def setup_database_async():
    DATABASE_URI = os.getenv('DATABASE_URI')
    if DATABASE_URI is None:
        raise ValueError("No DATABASE_URI set for the database. Set the DATABASE_URI environment variable.")

    engine = await asyncio.to_thread(create_async_engine,DATABASE_URI, echo=True)
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    Base = await asyncio.to_thread(declarative_base)

    return engine, SessionLocal, Base
