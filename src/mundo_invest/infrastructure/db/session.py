from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mundo_invest.infrastructure.config import get_settings

_settings = get_settings()
_connect_args = {"check_same_thread": False} if _settings.db_url.startswith("sqlite") else {}
engine = create_engine(_settings.db_url, future=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
