import secrets

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/arch_trainer"

    # ---- Auth0 (server-side BFF) ----
    # If auth0_domain is unset, the app falls back to a local dev-owner login so
    # it's usable without an Auth0 tenant. Set all four (+ owner_emails) in prod.
    auth0_domain: str | None = None
    auth0_client_id: str | None = None
    auth0_client_secret: str | None = None
    app_base_url: str = "http://localhost:8000"  # used to build the OIDC redirect_uri

    # Comma-separated emails allowed to spend the server's LLM keys (the only
    # users who can run generate/judge/AI-study). Everyone else is read/import only.
    owner_emails: str = ""

    # Signs the session cookie. Defaults to a random per-boot secret (you'll just
    # need to log in again after a restart); set it to keep sessions across reboots.
    session_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    # Send the session cookie only over HTTPS. Leave False for local http; True in prod.
    session_https_only: bool = False

    @property
    def auth0_configured(self) -> bool:
        return bool(self.auth0_domain and self.auth0_client_id and self.auth0_client_secret)

    @property
    def owner_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.owner_emails.split(",") if e.strip()}

    @field_validator("session_secret")
    @classmethod
    def _secret_fallback(cls, v: str) -> str:
        # An explicit empty env var must not become an empty signing key.
        return v or secrets.token_urlsafe(32)

    @field_validator("database_url")
    @classmethod
    def _use_psycopg3(cls, v: str) -> str:
        # Render/Heroku hand out bare postgres:// or postgresql:// URLs, which
        # SQLAlchemy routes to psycopg2. We ship psycopg v3 — force its driver.
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://") :]
        if v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v[len("postgresql://") :]
        return v

    # "provider:model_id" — see .env.example
    llm_model: str = "anthropic:claude-sonnet-4-6"

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    openrouter_api_key: str | None = None

    openai_base_url: str = "https://api.openai.com/v1"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Per-call LLM timeout (seconds) and retry cap. Keep the *effective* wait
    # (timeout × (retries+1)) below the frontend's 180s abort so a slow/queued
    # model returns a clean 504 ("model too slow") instead of the client aborting.
    # Retries are 0 because retrying a *timed-out* model just doubles the wait.
    llm_timeout: float = 90.0
    llm_max_retries: int = 0


settings = Settings()
