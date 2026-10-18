"""Athena configuration module."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for Athena.

    Values can be overridden by environment variables with the ATHENA_ prefix,
    or loaded from a local .env file.
    """

    model_config = SettingsConfigDict(
        env_prefix="ATHENA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_cache_mode: str = "off"
    llm_max_retries: int = 3
    llm_seed: int = 42

    # Budgets
    max_steps: int = 30
    max_tool_calls: int = 20
    max_tokens: int = 100000
    timeout_seconds: int = 300

    # Data limits & DuckDB
    max_file_size_mb: int = 50
    max_rows: int = 500000
    max_columns: int = 500
    sample_rows: int = 5
    sql_row_limit: int = 10000
    sql_timeout_seconds: int = 30
    duckdb_memory_limit: str = "512MB"

    # Machine Learning
    random_seed: int = 42
    shap_max_samples: int = 1000
    test_size: float = 0.2
    cv_folds: int = 5

    # Statistical Analysis
    alpha: float = 0.05

    # Verifier
    max_repair_iterations: int = 2
    numeric_tolerance_relative: float = 0.01
    numeric_tolerance_absolute: float = 0.005

    # Server & API
    host: str = "0.0.0.0"
    port: int = 8000
    demo_mode: bool = False
    demo_max_file_size_mb: int = 5
    demo_max_rows: int = 50000

    # Paths & Logging
    data_dir: str = "data"
    log_level: str = "INFO"

    @property
    def effective_max_file_size_mb(self) -> int:
        """Return effective max file size depending on demo mode."""
        return self.demo_max_file_size_mb if self.demo_mode else self.max_file_size_mb

    @property
    def effective_max_rows(self) -> int:
        """Return effective max rows depending on demo mode."""
        return self.demo_max_rows if self.demo_mode else self.max_rows


settings = Settings()
