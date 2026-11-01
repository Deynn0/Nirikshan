"""KMS-like Master Key Provider with rotation and environment/file persistence."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from nirikshan.config import settings


class MasterKeyError(Exception):
    """Base error for master key provider operations."""


class MasterKeyNotFoundError(MasterKeyError):
    """Raised when the specified master key ID does not exist."""


class MasterKeyProvider:
    """Provides envelope encryption master keys with support for key rotation.

    Keys can be sourced from:
    1. Direct in-memory registration.
    2. Environment variable (NIRIKSHAN_MASTER_KEYS or NIRIKSHAN_MASTER_KEY).
    3. KMS-like file store (trust/keys/master_keys.json).
    """

    def __init__(self, key_file_path: Path | None = None) -> None:
        self.key_file_path = key_file_path or settings.master_keys_json_path
        self._keys: dict[str, bytes] = {}
        self._active_key_id: str = settings.active_master_key_id
        self._load_keys()

    def _load_keys(self) -> None:
        """Load keys from file, environment, or generate default for offline testing."""
        # 1. Load from file if exists
        if self.key_file_path.exists():
            try:
                data = json.loads(self.key_file_path.read_text(encoding="utf-8"))
                for kid, b64_val in data.get("keys", {}).items():
                    self._keys[kid] = base64.b64decode(b64_val)
                if "active_key_id" in data and data["active_key_id"] in self._keys:
                    self._active_key_id = data["active_key_id"]
            except Exception as e:
                raise MasterKeyError(f"Failed to read master key file: {e}") from e

        # 2. Check environment variable override
        env_keys_json = os.environ.get("NIRIKSHAN_MASTER_KEYS")
        if env_keys_json:
            try:
                env_dict = json.loads(env_keys_json)
                for kid, b64_val in env_dict.items():
                    self._keys[kid] = base64.b64decode(b64_val)
            except Exception as e:
                raise MasterKeyError(f"Invalid NIRIKSHAN_MASTER_KEYS JSON in environment: {e}") from e

        single_env_key = os.environ.get(settings.master_key_env_var)
        if single_env_key:
            try:
                self._keys[settings.active_master_key_id] = base64.b64decode(single_env_key)
            except Exception:
                # If raw string is 32 bytes or utf-8
                key_bytes = single_env_key.encode("utf-8")
                if len(key_bytes) < 32:
                    key_bytes = key_bytes.ljust(32, b"#")[:32]
                self._keys[settings.active_master_key_id] = key_bytes[:32]

        # 3. If no keys exist at all, auto-provision the default active key
        if not self._keys:
            default_key = os.urandom(32)
            self._keys[self._active_key_id] = default_key
            self._persist_to_file()

    def _persist_to_file(self) -> None:
        """Persist current key set to key_file_path."""
        self.key_file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "active_key_id": self._active_key_id,
            "keys": {
                kid: base64.b64encode(kbytes).decode("ascii")
                for kid, kbytes in self._keys.items()
            },
        }
        self.key_file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @property
    def active_key_id(self) -> str:
        return self._active_key_id

    def get_active_key(self) -> tuple[str, bytes]:
        """Return the active (key_id, key_bytes) used for wrapping new document data keys."""
        if self._active_key_id not in self._keys:
            raise MasterKeyNotFoundError(f"Active master key '{self._active_key_id}' not found.")
        return self._active_key_id, self._keys[self._active_key_id]

    def get_key(self, key_id: str) -> bytes:
        """Retrieve a specific master key by ID (for unwrapping older documents)."""
        if key_id not in self._keys:
            raise MasterKeyNotFoundError(f"Master key '{key_id}' not found in provider.")
        return self._keys[key_id]

    def list_key_ids(self) -> list[str]:
        """List all available master key IDs."""
        return list(self._keys.keys())

    def rotate_master_key(
        self, new_key_id: str, new_key_bytes: bytes | None = None
    ) -> tuple[str, bytes]:
        """Provision a new active master key and set it as default for future documents.

        Previous master keys are retained so existing documents remain decryptable.
        """
        key_bytes = new_key_bytes or os.urandom(32)
        if len(key_bytes) != 32:
            raise MasterKeyError("Master key must be exactly 32 bytes (256 bits).")

        self._keys[new_key_id] = key_bytes
        self._active_key_id = new_key_id
        self._persist_to_file()
        return new_key_id, key_bytes

    def register_key(self, key_id: str, key_bytes: bytes, make_active: bool = False) -> None:
        """Register an existing key (e.g. for testing or migrations)."""
        if len(key_bytes) != 32:
            raise MasterKeyError("Master key must be exactly 32 bytes (256 bits).")
        self._keys[key_id] = key_bytes
        if make_active:
            self._active_key_id = key_id
        self._persist_to_file()


master_key_provider = MasterKeyProvider()
