from sqlalchemy import Column, String, Text, Integer, DateTime, func, UniqueConstraint
from .moretonbay import Base


class SenicRim(Base):
    __tablename__ = 'scenic_rim'
    id = Column(Integer, primary_key=True)
    application_id = Column(String(128), nullable=False, unique=True)

    category = Column(String(255), nullable=True, server_default=None)
    lodgement_date = Column(Integer, nullable=True)
    finalised_date = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(255), nullable=True, default=None)
    officer = Column(String(255), nullable=True, server_default=None)
    address = Column(Text, nullable=True, server_default=None)
    names = Column(String(255), nullable=True, server_default=None)
    documents = Column(Text, nullable=True, server_default=None)


    _tid = Column(String(255), nullable=False, server_default=None)
    created_at = Column(DateTime, server_default=func.now())
    update_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
