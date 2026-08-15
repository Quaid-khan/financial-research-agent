"""Unit tests for agent/config.py configuration loading and validation."""

import os
import pytest
from unittest.mock import patch
from agent.config import Settings, ConfigurationError, get_settings


def test_valid_configuration():
    """Test that valid settings initialize without error."""
    env_vars = {
        "ANTHROPIC_API_KEY": "sk-ant-api03-validkey123456",
        "SEC_EDGAR_USER_AGENT": "FinancialResearchAgent analyst@domain.com",
        "EMBEDDING_MODEL": "all-MiniLM-L6-v2",
        "CHROMA_DB_PATH": "./cache/chroma_db",
    }
    with patch.dict(os.environ, env_vars, clear=True):
        settings = get_settings()
        assert settings.anthropic_api_key == "sk-ant-api03-validkey123456"
        assert settings.sec_edgar_user_agent == "FinancialResearchAgent analyst@domain.com"
        assert settings.embedding_model == "all-MiniLM-L6-v2"


def test_missing_anthropic_api_key():
    """Test that missing ANTHROPIC_API_KEY raises ConfigurationError."""
    env_vars = {
        "ANTHROPIC_API_KEY": "",
        "SEC_EDGAR_USER_AGENT": "FinancialResearchAgent analyst@domain.com",
    }
    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY is missing"):
            get_settings()


def test_placeholder_anthropic_api_key():
    """Test that placeholder ANTHROPIC_API_KEY raises ConfigurationError."""
    env_vars = {
        "ANTHROPIC_API_KEY": "your_anthropic_api_key_here",
        "SEC_EDGAR_USER_AGENT": "FinancialResearchAgent analyst@domain.com",
    }
    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY is missing or unconfigured"):
            get_settings()


def test_invalid_sec_user_agent_format():
    """Test that SEC EDGAR User-Agent without email raises ConfigurationError."""
    env_vars = {
        "ANTHROPIC_API_KEY": "sk-ant-api03-validkey123456",
        "SEC_EDGAR_USER_AGENT": "FinancialResearchAgent NoEmailAddressHere",
    }
    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ConfigurationError, match="does not contain a valid contact email"):
            get_settings()


def test_placeholder_sec_user_agent():
    """Test that default placeholder SEC User-Agent raises ConfigurationError."""
    env_vars = {
        "ANTHROPIC_API_KEY": "sk-ant-api03-validkey123456",
        "SEC_EDGAR_USER_AGENT": "FinancialResearchAgent user@example.com",
    }
    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ConfigurationError, match="SEC_EDGAR_USER_AGENT must be configured"):
            get_settings()
