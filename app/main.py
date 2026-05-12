import secrets
import string

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Link
from app.schemas import LinkCreate, LinkResponse


app = FastAPI(title="LinkLibrary API")


Base.metadata.create_all(bind=engine) # Create the database tables based on the defined models. This will create the "links" table if it doesn't already exist.


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "LinkLibrary API is running",
    }


def generate_short_code(length: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length)) # Generate a random short code consisting of letters and digits. The length of the code can be specified (default is 6 characters). This function uses the secrets module to ensure that the generated code is cryptographically secure.

def get_link_by_url(db: Session, url: str) -> Link | None:
    return db.scalar(
        select(Link).where(Link.url == url) # Query the database to find a link entry that matches the given URL. If a matching link is found, it is returned; otherwise, None is returned.
    )
def get_link_by_code(db: Session, code: str) -> Link | None:
    return db.scalar(
        select(Link).where(Link.code == code) # Query the database to find a link entry that matches the given short code. If a matching link is found, it is returned; otherwise, None is returned.
    )


def generate_unique_short_code(db: Session, length: int = 6) -> str:
    while True:
        code = generate_short_code(length)

        existing_link = get_link_by_code(db, code)

        if existing_link is None:
            return code


def build_link_response(link: Link, request: Request) -> LinkResponse:
    return LinkResponse(
        code=link.code,
        url=link.url,
        short_url=str(request.url_for("redirect_to_link", code=link.code)),
        created_at=link.created_at,
    )


@app.post("/links", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
def create_link(
    link_create: LinkCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    url = str(link_create.url)

    existing_link = get_link_by_url(db, url
    )

    if existing_link is not None:
        response.status_code = status.HTTP_200_OK
        return build_link_response(existing_link, request)

    if link_create.custom_code is not None:
        existing_code_link = get_link_by_code(db, link_create.custom_code)

        if existing_code_link is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Short code already exists",
            )

        code = link_create.custom_code
    else:
        code = generate_unique_short_code(db)

    link = Link(
        code=code,
        url=url,
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    return build_link_response(link, request)


@app.get("/links", response_model=list[LinkResponse])
def list_links(
    request: Request,
    db: Session = Depends(get_db),
):
    links = db.scalars(
        select(Link).order_by(Link.created_at.desc())
    ).all()

    return [
        build_link_response(link, request)
        for link in links
    ]


@app.get("/{code}", name="redirect_to_link")
def redirect_to_link(
    code: str,
    db: Session = Depends(get_db),
):
    link = get_link_by_code(db, code)

    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found",
        )

    return RedirectResponse(url=link.url)