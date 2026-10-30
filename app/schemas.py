from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


# These paths belong to application routes.
RESERVED_CODES = frozenset({"links", "docs", "redoc"})


class LinkCreate(BaseModel):
    url: HttpUrl

    # Optional alias: 3–30 lowercase letters, digits, underscores or hyphens.
    custom_code: str | None = Field(
        default=None,
        min_length=3,
        max_length=30,
        pattern=r"^[a-z0-9_-]+$",
    )

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, value: str | None) -> str | None:
        # Prevent aliases from overlapping application routes.
        if value in RESERVED_CODES:
            raise ValueError("This short code is reserved")

        return value


# Public fields returned when creating or listing links.
class LinkResponse(BaseModel):
    code: str
    url: str
    short_url: str
    created_at: datetime