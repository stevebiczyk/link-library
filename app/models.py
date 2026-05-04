from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class Link(Base):
    __tablename__ = "links"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) # Unique identifier for each link entry. This is an auto-incrementing integer and serves as the primary key in the database.
    code: Mapped[str] = mapped_column(String, unique=True, index=True) # The short code that maps to the original URL. This is a string that must be unique across all entries in the database.
    url: Mapped[str] = mapped_column(String) # The original URL that the short code points to. This is stored as a string.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False) # Timestamp indicating when the link was created. This is automatically set to the current UTC time when a new link entry is created.
    