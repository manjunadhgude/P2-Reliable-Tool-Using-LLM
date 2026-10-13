from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[3] / ".env", extra="ignore")
    app_name: str = "P2 Business Operations Assistant"
    database_url: str = "sqlite:///./p2.db"
    demo_signing_secret: str = "local-demo-only-change-before-deployment"
    model_backend: str = "deterministic_test"
    hybrid_controller_enabled: bool = False
    # Version switch for bounded, opt-in controller experiments. Default remains
    # the existing v2 path; candidates are never selected implicitly.
    hybrid_controller_version: str = "v2"
    model_id: str = "Qwen/Qwen3-1.7B"
    model_revision: str = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
    ollama_url: str = "http://localhost:11434"
    cors_origins: str = "http://localhost:5173"
    max_model_steps: int = 5
    max_tool_calls: int = 4
    max_output_repair_retries: int = 1
    model_max_new_tokens: int = 256
    request_timeout_seconds: int = 30


settings = Settings()
