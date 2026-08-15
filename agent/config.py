"""Environment configuration and settings validation for Financial Research Agent.

This module loads environment variables via python-dotenv, validates required
API keys and settings using Pydantic, and exposes a centralized Config object.
"""

import os
import re
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ValidationError


class ConfigurationError(Exception):
    """Raised when required environment variables are missing or invalid."""
    pass


# Load .env file from root directory if present
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseModel):
    """Pydantic model validating system configuration and API keys."""

    # Google Gemini LLM Settings (Free Tier)
    gemini_api_key: str = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", ""),
        description="Google Gemini API key obtained from https://aistudio.google.com/apikey",
        validate_default=True
    )
    gemini_model: str = Field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        description="Gemini LLM model identifier (Default: gemini-3.6-flash)."
    )

    # SEC EDGAR Requirements
    sec_edgar_user_agent: str = Field(
        default_factory=lambda: os.getenv("SEC_EDGAR_USER_AGENT", ""),
        description="User-Agent header required by SEC EDGAR (Format: 'Name email@domain.com').",
        validate_default=True
    )

    # Embeddings & Vector DB Settings
    embedding_model: str = Field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        description="HuggingFace sentence-transformers model name."
    )
    chroma_db_path: str = Field(
        default_factory=lambda: os.getenv("CHROMA_DB_PATH", "./cache/chroma_db"),
        description="Local directory path for persistent ChromaDB storage."
    )

    # Financial Data Provider Keys (Optional)
    fmp_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("FMP_API_KEY", None),
        description="Financial Modeling Prep API key (Optional)."
    )
    alpha_vantage_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("ALPHA_VANTAGE_API_KEY", None),
        description="Alpha Vantage API key (Optional)."
    )
    finnhub_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("FINNHUB_API_KEY", None),
        description="Finnhub API key (Optional)."
    )

    # Logging & Caching
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
        description="Application logging verbosity."
    )
    cache_dir: str = Field(
        default_factory=lambda: os.getenv("CACHE_DIR", "./cache"),
        description="Directory path for HTTP and raw data caching."
    )

    @field_validator("gemini_api_key", mode="after")
    @classmethod
    def validate_gemini_key(cls, value: str) -> str:
        """Ensure Gemini API key is provided and not a placeholder."""
        cleaned = (value or "").strip()
        if not cleaned or cleaned.startswith("your_") or cleaned == "placeholder":
            raise ValueError(
                "GEMINI_API_KEY is missing or unconfigured in .env file. "
                "Obtain a free key at https://aistudio.google.com/apikey and add it to .env"
            )
        return cleaned

    @field_validator("sec_edgar_user_agent", mode="after")
    @classmethod
    def validate_sec_user_agent(cls, value: str) -> str:
        """Validate SEC EDGAR User-Agent format per SEC Fair Access requirements."""
        cleaned = (value or "").strip()
        if not cleaned or "user@example.com" in cleaned or "your.email" in cleaned:
            raise ValueError(
                "SEC_EDGAR_USER_AGENT must be configured in .env with a valid identity "
                "and email address (e.g., 'FinancialResearchAgent admin@yourdomain.com')."
            )
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        if not re.search(email_pattern, cleaned):
            raise ValueError(
                f"SEC_EDGAR_USER_AGENT '{cleaned}' does not contain a valid contact email address. "
                "Format requirement: 'Organization/App Name contact@domain.com'"
            )
        return cleaned


def get_settings() -> Settings:
    """Instantiate and validate settings from environment variables.
    
    Returns:
        Settings: Validated configuration instance.
        
    Raises:
        ConfigurationError: If any required setting is missing or invalid.
    """
    try:
        return Settings()
    except ConfigurationError:
        raise
    except ValidationError as val_err:
        messages = []
        for error in val_err.errors():
            msg = error.get("msg", "")
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, "):]
            messages.append(msg)
        raise ConfigurationError("\n".join(messages)) from val_err
    except Exception as err:
        raise ConfigurationError(f"Failed to load project configuration: {err}") from err
