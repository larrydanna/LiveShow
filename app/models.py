from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.database import Base


class AppConfig(Base):
    __tablename__ = "app_config"

    key = Column(String(64), primary_key=True)
    value = Column(String(256), nullable=False)


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    body = Column(Text, nullable=False)
    submitted_by = Column(String(48), nullable=False)
    font_face = Column(String(256), nullable=True)
    font_size = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ScriptQueue(Base):
    __tablename__ = "script_queues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ScriptQueueItem(Base):
    __tablename__ = "script_queue_items"

    id = Column(Integer, primary_key=True, index=True)
    queue_id = Column(Integer, ForeignKey("script_queues.id"), nullable=False)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    position = Column(Integer, default=0)
