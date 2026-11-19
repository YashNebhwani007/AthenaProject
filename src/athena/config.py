"""Athena configuration module."""

from pydantic import Field
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
    llm_provider: str = Field(default="groq", description="LLM provider name (e.g. groq, gemini)")
    llm_model: str = Field(default="llama-3.3-70b-versatile", description="Model identifier")
    llm_api_key: str = Field(default="", description="API key for LLM service")
    llm_base_url: str = Field(default="https://api.groq.com/openai/v1", description="Endpoint URL")
    llm_cache_mode: str = Field(default="off", description="LLM response cache mode")
    llm_max_retries: int = Field(default=3, description="Maximum API retry attempts")
    llm_seed: int = Field(default=42, description="Deterministic seed for generation")

    # Budgets
    max_steps: int = Field(default=30, description="Max tool-calling orchestration steps")
    max_tool_calls: int = Field(default=20, description="Max tool calls per session")
    max_tokens: int = Field(default=100000, description="Max token allowance")
    timeout_seconds: int = Field(default=300, description="Overall timeout in seconds")

    # Data limits & DuckDB
    max_file_size_mb: int = Field(default=50, description="Max uploaded file size in MB")
    max_rows: int = Field(default=500000, description="Max rows loaded into DuckDB")
    max_columns: int = Field(default=500, description="Max columns allowed in dataset")
    sample_rows: int = Field(default=5, description="Number of sample values per column")
    sql_row_limit: int = Field(default=10000, description="Max rows returned by SQL query")
    sql_timeout_seconds: int = Field(default=30, description="Timeout for SQL queries")
    duckdb_memory_limit: str = Field(default="512MB", description="DuckDB max memory limit")

    # Machine Learning
    random_seed: int = Field(default=42, description="Random seed for ML train/test splitting")
    shap_max_samples: int = Field(default=1000, description="Max samples for SHAP explainability")
    test_size: float = Field(default=0.2, description="Fraction of data for held-out testing")
    cv_folds: int = Field(default=5, description="Cross-validation fold count")

    # Statistical Analysis
    alpha: float = Field(default=0.05, description="Significance threshold for hypothesis tests")

    # Verifier
    max_repair_iterations: int = Field(default=2, description="Max repair attempts in verifier")
    numeric_tolerance_relative: float = Field(
        default=0.01, description="V1 relative tolerance (1%)"
    )
    numeric_tolerance_absolute: float = Field(
        default=0.005, description="V1 absolute tolerance (0.005)"
    )

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
