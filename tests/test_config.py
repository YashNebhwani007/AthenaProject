"""Tests for Athena configuration module."""

import pytest

from athena.config import Settings, settings


def test_default_settings():
    """Verify all default configuration values match specification."""
    s = Settings()

    # LLM defaults
    assert s.llm_provider == "groq"
    assert s.llm_model == "llama-3.3-70b-versatile"
    assert s.llm_api_key == ""
    assert s.llm_base_url == "https://api.groq.com/openai/v1"
    assert s.llm_cache_mode == "off"
    assert s.llm_max_retries == 3
    assert s.llm_seed == 42

    # Budgets
    assert s.max_steps == 30
    assert s.max_tool_calls == 20
    assert s.max_tokens == 100000
    assert s.timeout_seconds == 300

    # Data
    assert s.max_file_size_mb == 50
    assert s.max_rows == 500000
    assert s.max_columns == 500
    assert s.sample_rows == 5
    assert s.sql_row_limit == 10000
    assert s.sql_timeout_seconds == 30
    assert s.duckdb_memory_limit == "512MB"

    # ML
    assert s.random_seed == 42
    assert s.shap_max_samples == 1000
    assert s.test_size == 0.2
    assert s.cv_folds == 5

    # Stats
    assert s.alpha == 0.05

    # Verifier
    assert s.max_repair_iterations == 2
    assert s.numeric_tolerance_relative == 0.01
    assert s.numeric_tolerance_absolute == 0.005

    # Server
    assert s.host == "0.0.0.0"
    assert s.port == 8000
    assert s.demo_mode is False
    assert s.demo_max_file_size_mb == 5
    assert s.demo_max_rows == 50000

    # Paths & Logging
    assert s.data_dir == "data"
    assert s.log_level == "INFO"


def test_module_settings_instance():
    """Verify module-level settings singleton is instantiated."""
    assert isinstance(settings, Settings)


def test_env_var_overrides(monkeypatch: pytest.MonkeyPatch):
    """Verify settings can be overridden via ATHENA_ environment variables."""
    monkeypatch.setenv("ATHENA_LLM_PROVIDER", "openai")
    monkeypatch.setenv("ATHENA_LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("ATHENA_LLM_API_KEY", "sk-secret-key-123")
    monkeypatch.setenv("ATHENA_LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("ATHENA_LLM_CACHE_MODE", "record")
    monkeypatch.setenv("ATHENA_LLM_MAX_RETRIES", "5")
    monkeypatch.setenv("ATHENA_LLM_SEED", "7")
    monkeypatch.setenv("ATHENA_MAX_STEPS", "15")
    monkeypatch.setenv("ATHENA_MAX_TOOL_CALLS", "10")
    monkeypatch.setenv("ATHENA_MAX_TOKENS", "50000")
    monkeypatch.setenv("ATHENA_TIMEOUT_SECONDS", "120")
    monkeypatch.setenv("ATHENA_ALPHA", "0.01")
    monkeypatch.setenv("ATHENA_PORT", "9000")
    monkeypatch.setenv("ATHENA_DEMO_MODE", "true")

    s = Settings()
    assert s.llm_provider == "openai"
    assert s.llm_model == "gpt-4o-mini"
    assert s.llm_api_key == "sk-secret-key-123"
    assert s.llm_base_url == "https://api.openai.com/v1"
    assert s.llm_cache_mode == "record"
    assert s.llm_max_retries == 5
    assert s.llm_seed == 7
    assert s.max_steps == 15
    assert s.max_tool_calls == 10
    assert s.max_tokens == 50000
    assert s.timeout_seconds == 120
    assert s.alpha == 0.01
    assert s.port == 9000
    assert s.demo_mode is True


def test_demo_limits():
    """Verify effective limits adapt based on demo_mode."""
    standard_settings = Settings(demo_mode=False)
    assert standard_settings.effective_max_file_size_mb == 50
    assert standard_settings.effective_max_rows == 500000

    demo_settings = Settings(demo_mode=True)
    assert demo_settings.effective_max_file_size_mb == 5
    assert demo_settings.effective_max_rows == 50000

    custom_demo_settings = Settings(
        demo_mode=True,
        demo_max_file_size_mb=2,
        demo_max_rows=10000,
    )
    assert custom_demo_settings.effective_max_file_size_mb == 2
    assert custom_demo_settings.effective_max_rows == 10000
