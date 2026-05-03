import secrets # For generating secure random short codes
import string

from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

app = FastAPI(title="LinkLibrary API")

links : dict[str, str] = {} # In-memory storage for short code to URL mapping. 

class LinkCreate(BaseModel):
    url: HttpUrl
    
class LinkResponse(BaseModel):
    code: str
    url: str
    short_url: str
    
@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "LinkLibrary API is running",
    }
    
def generate_short_code(length: int = 6) -> str: # Function to generate a unique short code of specified length (default is 6)
    alphabet = string.ascii_letters + string.digits # This includes uppercase, lowercase letters and string.digits
    
    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(length)) # Generate a random code of the specified length
        if code not in links:
            return code
        
        
@app.post("/links", response_model=LinkResponse)
def create_link(link: LinkCreate): # Endpoint to create a new short link. It takes a LinkCreate object as input, generates a unique short code, and stores the mapping in the links dictionary. It returns a LinkResponse object containing the short code, original URL, and the short URL path.
    code = generate_short_code()
    url = str(link.url)
    links[code] = url
    
    return LinkResponse(
        code=code,
        url=url,
        short_url=f"/{code}"
    )
    
@app.get("/links", response_model=dict[str, str])
def list_links():
    return links
