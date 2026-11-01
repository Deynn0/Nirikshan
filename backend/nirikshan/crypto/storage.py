"""Encrypted Storage Service storing per-document encrypted envelopes in quarantine."""

from __future__ import annotations

from pathlib import Path

from nirikshan.config import settings
from nirikshan.crypto.envelope import (
    EncryptedDocumentEnvelope,
    decrypt_envelope,
    encrypt_envelope,
    rewrap_envelope,
)
from nirikshan.crypto.master_keys import MasterKeyProvider, master_key_provider


class EncryptedStorageService:
    """Storage service managing encrypted envelopes on disk.

    Enforces that documents are stored encrypted at rest and can only be transparently
    decrypted within an authorized isolated sandbox subprocess.
    """

    def __init__(
        self,
        storage_dir: Path | None = None,
        key_provider: MasterKeyProvider | None = None,
    ) -> None:
        self.storage_dir = storage_dir or settings.quarantine_dir
        self.key_provider = key_provider or master_key_provider
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def get_envelope_path(self, document_id: str) -> Path:
        return self.storage_dir / f"{document_id}.enc.json"

    def store_document(
        self,
        document_id: str,
        plaintext: bytes,
    ) -> tuple[Path, EncryptedDocumentEnvelope]:
        """Encrypt document with unique DEK, wrap with active master key, and persist envelope."""
        envelope = encrypt_envelope(
            document_id=document_id,
            plaintext=plaintext,
            provider=self.key_provider,
        )
        path = self.get_envelope_path(document_id)
        path.write_text(envelope.to_json(), encoding="utf-8")
        return path, envelope

    def load_envelope(self, target: str | Path) -> EncryptedDocumentEnvelope:
        """Load envelope from document ID or file path."""
        path = Path(target) if isinstance(target, Path) or ("/" in str(target) or "\\" in str(target)) else self.get_envelope_path(str(target))
        if not path.exists():
            raise FileNotFoundError(f"Encrypted envelope not found: {path}")
        return EncryptedDocumentEnvelope.from_json(path.read_text(encoding="utf-8"))

    def decrypt_document(
        self,
        target: str | Path | EncryptedDocumentEnvelope,
        is_sandbox: bool = False,
    ) -> bytes:
        """Transparently decrypt document envelope (strictly inside sandbox environment)."""
        if isinstance(target, EncryptedDocumentEnvelope):
            envelope = target
        else:
            envelope = self.load_envelope(target)

        return decrypt_envelope(
            envelope=envelope,
            provider=self.key_provider,
            is_sandbox=is_sandbox,
        )

    def rewrap_document(
        self,
        document_id: str,
        new_master_key_id: str | None = None,
    ) -> EncryptedDocumentEnvelope:
        """Rotate master key wrapping for a stored document."""
        path = self.get_envelope_path(document_id)
        envelope = self.load_envelope(path)
        new_envelope = rewrap_envelope(
            envelope=envelope,
            new_master_key_id=new_master_key_id,
            provider=self.key_provider,
        )
        path.write_text(new_envelope.to_json(), encoding="utf-8")
        return new_envelope


encrypted_storage = EncryptedStorageService()
