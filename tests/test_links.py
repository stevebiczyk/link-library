from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite://" # Use an in-memory SQLite database for testing.

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, # Use StaticPool to ensure that the same in-memory database is used across multiple connections.
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=engine) # Drop all tables to ensure a clean state for each test.
    Base.metadata.create_all(bind=engine) # Create the tables based on the defined models.
    
    db = TestingSessionLocal() # Create a new database session for the test.
    try:
        yield db # Yield the session to be used in the test.
    finally:
        db.close() # Close the session after the test is done.
        Base.metadata.drop_all(bind=engine) # Drop all tables again to clean up after the test.
        
@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session  # Override the get_db dependency to use the test database session.
        
    app.dependency_overrides[get_db] = override_get_db  # Override the get_db dependency in the FastAPI app to use the test database session.
        
    with TestClient(app) as test_client:  # Create a TestClient for the FastAPI app to simulate HTTP requests in tests.
        yield test_client  # Yield the TestClient to be used in the test.
        
    app.dependency_overrides.clear()  # Clear the dependency overrides after the test is done to avoid affecting other tests.
    

def test_create_link_returns_short_link(client: TestClient): # Test that creating a new link returns the expected short link response.
    response = client.post(
        "/links",
        json={"url": "https://example.com"},
    )
            
    assert response.status_code == 201
    data = response.json()
            
    assert "code" in data
    assert len(data["code"]) == 6
    assert data["url"] == "https://example.com/"
    assert data["short_url"].endswith(f"/{data['code']}")
    assert "created_at" in data
            

def test_list_links_returns_created_links(client: TestClient): # Test that the list links endpoint returns the links that have been created.
    create_response = client.post(
        "/links",
        json={"url": "https://example.com"},
    )

    created_link = create_response.json()

    list_response = client.get("/links")

    assert list_response.status_code == 200

    links = list_response.json()

    assert len(links) == 1
    assert links[0]["code"] == created_link["code"]
    assert links[0]["url"] == "https://example.com/"
    assert links[0]["short_url"].endswith(f"/{created_link['code']}")


def test_redirect_to_saved_link(client: TestClient): # Test that accessing the short URL redirects to the original URL.
    create_response = client.post(
        "/links",
        json={"url": "https://example.com"},
    )

    created_link = create_response.json()
    code = created_link["code"]

    redirect_response = client.get(
        f"/{code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == created_link["url"]


def test_unknown_short_code_returns_404(client: TestClient): # Test that accessing a non-existent short code returns a 404 error.
    response = client.get(
        "/does-not-exist",
        follow_redirects=False,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Short link not found"}


def test_create_link_rejects_invalid_url(client: TestClient): # Test that creating a link with an invalid URL returns a 422 error.
    response = client.post(
        "/links",
        json={"url": "not-a-valid-url"},
    )

    assert response.status_code == 422
    
def test_create_same_url_twice_returns_existing_link(client: TestClient):
    first_response = client.post(
        "/links",
        json={"url": "https://example.com"},
    )

    second_response = client.post(
        "/links",
        json={"url": "https://example.com"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 200

    first_link = first_response.json()
    second_link = second_response.json()

    assert second_link["code"] == first_link["code"]
    assert second_link["url"] == first_link["url"]
    assert second_link["short_url"] == first_link["short_url"]

    list_response = client.get("/links")
    links = list_response.json()

    assert len(links) == 1
    
def test_create_link_with_custom_code(client: TestClient): # Test that creating a link with a custom code works as expected.
    response = client.post(
        "/links",
        json={"url": "https://github.com", "custom_code": "github"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["code"] == "github"
    assert data["url"] == "https://github.com/"
    assert data["short_url"].endswith("/github")
    assert "created_at" in data
    
def test_custom_code_redirects_to_saved_link(client: TestClient): # Test that accessing a custom short code redirects to the original URL.
    create_response = client.post(
        "/links",
        json={"url": "https://github.com", "custom_code": "github"},
    )
    
    assert create_response.status_code == 201

    redirect_response = client.get(
        "/github",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://github.com/"
    
def test_duplicate_custom_code_returns_409(client: TestClient): # Test that trying to create a link with a custom code that already exists returns a 409 error.
    first_response = client.post(
        "/links",
        json={"url": "https://github.com", "custom_code": "github"},
    )

    second_response = client.post(
        "/links",
        json={"url": "https://example.com", "custom_code": "github"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "Short code already exists"}
        
def test_invalid_custom_code_is_rejected(client: TestClient): # Test that trying to create a link with an invalid custom code returns a 422 error.
    response = client.post(
        "/links",
        json={"url": "https://example.com", "custom_code": "invalid code!"},
    )

    assert response.status_code == 422