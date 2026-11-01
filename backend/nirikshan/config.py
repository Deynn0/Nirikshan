"""Nirikshan configuration module."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """System settings for offline scrutiny execution."""

    app_name: str = "Nirikshan Regulatory Scrutiny System"
    app_version: str = "0.1.0"
    debug: bool = False

    # Storage paths (Relative to backend root or absolute)
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "var"
    rulesets_dir: Path = base_dir / "rulesets"
    quarantine_dir: Path = base_dir / "var" / "quarantine"
    parsed_cache_dir: Path = base_dir / "var" / "parsed_cache"
    trust_dir: Path = base_dir / "trust"
    trust_roots_dir: Path = trust_dir / "roots"
    issuers_yaml_path: Path = trust_dir / "issuers.yaml"
    keyring_json_path: Path = trust_dir / "keyring.json"

    # SQLite Database
    database_url: str = f"sqlite+aiosqlite:///{base_dir}/var/nirikshan.db"
    database_sync_url: str = f"sqlite:///{base_dir}/var/nirikshan.db"

    # Strict Sandbox Security Limits
    worker_timeout_seconds: int = 45
    worker_max_memory_mb: int = 512
    max_upload_size_mb: int = 50
    allowed_mimetypes: list[str] = ["application/pdf", "image/png", "image/jpeg"]
    sandbox_cpu_limit_seconds: int = 15
    sandbox_memory_limit_mb: int = 512
    sandbox_wall_clock_timeout_seconds: int = 20
    sandbox_max_file_size_bytes: int = 50 * 1024 * 1024
    sandbox_max_page_count: int = 100
    sandbox_max_decompression_ratio: float = 30.0

    # Master Key and Envelope Encryption Settings
    master_keys_dir: Path = trust_dir / "keys"
    master_keys_json_path: Path = trust_dir / "master_keys.json"
    active_master_key_id: str = "master-key-2024-v1"
    master_key_env_var: str = "NIRIKSHAN_MASTER_KEY"

    # Auth & Rate Limiting Settings
    rate_limit_per_minute: int = 120
    jwt_secret_key: str = "nirikshan-hardened-airgap-jwt-secret-2024"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Advisory ML Layer Settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"
    models_dir: Path = base_dir / "var" / "models"
    yolox_model_path: Path = base_dir / "var" / "models" / "yolox_m.onnx"

    # Regulatory Edition
    active_handbook_edition: str = "AICTE Approval Process Handbook 2024-2027"

    # Zero-telemetry / Offline enforcement
    allow_external_network: bool = False

    # Cross-Application Fraud Graph Settings
    fraud_salt: str = "nirikshan-secret-salt-2024"
    fraud_photo_hamming_threshold: int = 6
    fraud_seal_hamming_threshold: int = 5
    fraud_address_similarity_threshold: float = 0.85
    fraud_allow_shared_parent_trust: bool = True

    model_config = SettingsConfigDict(env_prefix="NIRIKSHAN_", extra="ignore")

    def ensure_directories(self) -> None:
        """Ensure all required local storage directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.rulesets_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.parsed_cache_dir.mkdir(parents=True, exist_ok=True)
        self.trust_dir.mkdir(parents=True, exist_ok=True)
        self.trust_roots_dir.mkdir(parents=True, exist_ok=True)
        self.master_keys_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
