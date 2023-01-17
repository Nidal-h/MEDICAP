from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


if TYPE_CHECKING:
    from .user import User  # noqa: F401
    from .voice import Voice  # noqa: F401


class RemarqueNote(Base):
    id = Column(Integer, primary_key=True, index=True)
    
    remarque = Column(String, index=True)
    seen = Column(Boolean(), default=False)
    
    note_id = Column(Integer, ForeignKey("note.id"))
    note = relationship("Note", foreign_keys=[note_id], backref=backref("note", uselist=False))

    creator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    date_creation = Column(DateTime, nullable= False)