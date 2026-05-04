from datetime import datetime
from pydantic import BaseModel, HttpUrl

class LinkCreate(BaseModel):
    url: HttpUrl # The original URL that the user wants to shorten. This field is required and must be a valid URL format.
    
class LinkResponse(BaseModel):
    code: str # The unique short code generated for the original URL. This is a string that serves as the identifier for the shortened link.
    url: str # The original URL that the short code points to. This is stored as a string.
    short_url: str # The full short URL that can be used to access the original URL. This is typically constructed by combining the base URL of the service with the short code (e.g., "http://localhost:8000/{code}").
    created_at: datetime # Timestamp indicating when the link was created. This is automatically set to the current UTC time when a new link entry is created.