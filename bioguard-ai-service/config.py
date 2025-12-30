"""
BioGuard AI Service Configuration
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    # Agent Configuration
    agent_max_iterations: int = 10
    agent_temperature: float = 0.1

    # Policy Configuration
    policy_strict_mode: bool = True  # If true, policy floor is always enforced

    # Feature Store Configuration
    feature_store_type: str = "memory"  # "memory" or "redis"
    redis_url: Optional[str] = os.getenv("REDIS_URL", None)

    # Risk Thresholds (default values, can be overridden per merchant)
    risk_threshold_allow: float = 0.3
    risk_threshold_stepup: float = 0.5
    risk_threshold_hold: float = 0.7
    risk_threshold_block: float = 0.85

    # Scoring Weights
    weight_integrity: float = 0.30
    weight_lightsync: float = 0.25
    weight_liveness: float = 0.25
    weight_behavior: float = 0.10
    weight_context: float = 0.10

    # API Configuration
    api_prefix: str = "/v1"
    debug_mode: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Notification Configuration
    webhook_timeout_seconds: int = 10
    webhook_retry_count: int = 3

    # Case Configuration
    auto_create_case_on_hold: bool = True
    auto_create_case_on_block: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


# Merchant-specific configuration (can be extended to database)
MERCHANT_CONFIGS = {
    "default": {
        "name": "Default Merchant",
        "risk_thresholds": {
            "allow": 0.3,
            "stepup": 0.5,
            "hold": 0.7,
            "block": 0.85,
        },
        "enabled_checks": ["integrity", "lightsync", "liveness", "behavior"],
        "webhook_url": None,
    },
    "bank_demo": {
        "name": "Demo Bank",
        "risk_thresholds": {
            "allow": 0.25,  # Stricter
            "stepup": 0.45,
            "hold": 0.65,
            "block": 0.80,
        },
        "enabled_checks": ["integrity", "lightsync", "liveness", "behavior"],
        "webhook_url": "https://webhook.example.com/bioguard",
    },
}


def get_merchant_config(merchant_id: str) -> dict:
    """Get merchant-specific configuration"""
    return MERCHANT_CONFIGS.get(merchant_id, MERCHANT_CONFIGS["default"])
