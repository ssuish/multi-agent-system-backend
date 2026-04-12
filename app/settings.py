from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        ...,
        description="Supabase Postgres URI"
    ),
    clerk_jwks_url: str = Field(
        ...,
        description="Clerk JWKS URL"
    ),
    clerk_issuer: str = Field(
        ...,
        description="JWT iss claim"
    ),
    clerk_audience: str | None = Field(
        None,
        description="Optional azp/aud verification; set if use a named audience."
    ),
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed browser origins."
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.split()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
