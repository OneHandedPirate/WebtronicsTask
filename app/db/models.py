import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)


class Post(Base):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    author_id = Column(UUID, ForeignKey("user.uuid", ondelete="CASCADE"))


class Vote(Base):
    __tablename__ = 'vote'

    user_uuid = Column(UUID, ForeignKey("user.uuid", ondelete="CASCADE"),
                       primary_key=True, nullable=False)
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"),
                     primary_key=True, nullable=False)
    is_like = Column(Boolean, nullable=False)




