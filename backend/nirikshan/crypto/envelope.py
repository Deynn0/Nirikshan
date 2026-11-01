"""Envelope encryption implementation with AES-256-GCM data keys and master key wrapping."""

from __future__ import annotations

import base64
import hashlib
import os
from datetime import UTC, datetime

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import BaseModel, Field

from nirikshan.crypto.master_keys import MasterKeyProvider, master_key_provider


class EnvelopeEncryptionError(Exception):
    """Base error for envelope encryption operations."""


class EnvelopeTamperError(EnvelopeEncryptionError):
    """Raised when authentication tag verification or hash check fails (tampered payload)."""


class SandboxDecryptionEnforcementError(EnvelopeEncryptionError):
    """Raised when decryption is attempted outside of the authorized sandbox environment."""


class EncryptedDocumentEnvelope(BaseModel):
    """Cryptographic envelope storing per-document AES-256-GCM ciphertext and wrapped DEK."""

    version: int = 1
    document_id: str
    master_key_id: str
    dek_nonce_b64: str
    wrapped_dek_b64: str
    doc_nonce_b64: str
    doc_ciphertext_b64: str
    plaintext_sha256: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> EncryptedDocumentEnvelope:
        return cls.model_validate_json(json_str)


def encrypt_envelope(
    document_id: str,
    plaintext: bytes,
    provider: MasterKeyProvider | None = None,
) -> EncryptedDocumentEnvelope:
    """Generate per-document 256-bit DEK, encrypt document with AES-256-GCM, and wrap DEK with active master key."""
    mk_provider = provider or master_key_provider
    master_key_id, master_key = mk_provider.get_active_key()

    # 1. Generate unique per-document DEK (32 bytes = 256 bits)
    dek = os.urandom(32)

    # 2. Encrypt plaintext document using DEK with AES-256-GCM
    doc_nonce = os.urandom(12)
    doc_aesgcm = AESGCM(dek)
    doc_aad = f"doc:{document_id}".encode()
    doc_ciphertext = doc_aesgcm.encrypt(doc_nonce, plaintext, doc_aad)

    # 3. Wrap DEK using Master Key with AES-256-GCM
    dek_nonce = os.urandom(12)
    master_aesgcm = AESGCM(master_key)
    dek_aad = f"dek:{document_id}:{master_key_id}".encode()
    wrapped_dek = master_aesgcm.encrypt(dek_nonce, dek, dek_aad)

    # 4. Compute plaintext digest for end-to-end verification
    sha256_hash = hashlib.sha256(plaintext).hexdigest()

    return EncryptedDocumentEnvelope(
        version=1,
        document_id=document_id,
        master_key_id=master_key_id,
        dek_nonce_b64=base64.b64encode(dek_nonce).decode("ascii"),
        wrapped_dek_b64=base64.b64encode(wrapped_dek).decode("ascii"),
        doc_nonce_b64=base64.b64encode(doc_nonce).decode("ascii"),
        doc_ciphertext_b64=base64.b64encode(doc_ciphertext).decode("ascii"),
        plaintext_sha256=sha256_hash,
    )


def decrypt_envelope(
    envelope: EncryptedDocumentEnvelope,
    provider: MasterKeyProvider | None = None,
    is_sandbox: bool = False,
) -> bytes:
    """Unwrap DEK and decrypt document ciphertext inside the authorized sandbox environment only."""
    # Enforce strict sandbox isolation guarantee: decryption is permitted only in sandbox
    sandbox_active = is_sandbox or (os.environ.get("NIRIKSHAN_SANDBOX_ACTIVE") == "1")
    if not sandbox_active:
        raise SandboxDecryptionEnforcementError(
            "Access Denied: Document decryption is restricted strictly to isolated sandbox workers."
        )

    mk_provider = provider or master_key_provider
    try:
        master_key = mk_provider.get_key(envelope.master_key_id)
    except Exception as e:
        raise EnvelopeEncryptionError(
            f"Failed to locate master key '{envelope.master_key_id}': {e}"
        ) from e

    # 1. Unwrap DEK using Master Key
    try:
        dek_nonce = base64.b64decode(envelope.dek_nonce_b64)
        wrapped_dek = base64.b64decode(envelope.wrapped_dek_b64)
        master_aesgcm = AESGCM(master_key)
        dek_aad = f"dek:{envelope.document_id}:{envelope.master_key_id}".encode()
        dek = master_aesgcm.decrypt(dek_nonce, wrapped_dek, dek_aad)
    except InvalidTag as e:
        raise EnvelopeTamperError(
            "Cryptographic tamper detected: Wrapped DEK authentication tag verification failed."
        ) from e
    except Exception as e:
        raise EnvelopeTamperError(f"DEK unwrap failed: {e}") from e

    # 2. Decrypt document using DEK
    try:
        doc_nonce = base64.b64decode(envelope.doc_nonce_b64)
        doc_ciphertext = base64.b64decode(envelope.doc_ciphertext_b64)
        doc_aesgcm = AESGCM(dek)
        doc_aad = f"doc:{envelope.document_id}".encode()
        plaintext = doc_aesgcm.decrypt(doc_nonce, doc_ciphertext, doc_aad)
    except InvalidTag as e:
        raise EnvelopeTamperError(
            "Cryptographic tamper detected: Document ciphertext authentication tag mismatch."
        ) from e
    except Exception as e:
        raise EnvelopeTamperError(f"Document decrypt failed: {e}") from e

    # 3. Verify digest matches expected plaintext SHA-256
    computed_digest = hashlib.sha256(plaintext).hexdigest()
    if computed_digest != envelope.plaintext_sha256:
        raise EnvelopeTamperError(
            f"Plaintext integrity mismatch: computed {computed_digest} vs expected {envelope.plaintext_sha256}"
        )

    return plaintext


def rewrap_envelope(
    envelope: EncryptedDocumentEnvelope,
    new_master_key_id: str | None = None,
    provider: MasterKeyProvider | None = None,
) -> EncryptedDocumentEnvelope:
    """Rotate the master key wrapping a document's DEK without re-encrypting the document ciphertext."""
    mk_provider = provider or master_key_provider
    target_key_id = new_master_key_id or mk_provider.active_key_id

    # 1. Unwrap DEK with original master key
    old_master_key = mk_provider.get_key(envelope.master_key_id)
    dek_nonce = base64.b64decode(envelope.dek_nonce_b64)
    wrapped_dek = base64.b64decode(envelope.wrapped_dek_b64)
    master_aesgcm = AESGCM(old_master_key)
    dek_aad = f"dek:{envelope.document_id}:{envelope.master_key_id}".encode()

    try:
        dek = master_aesgcm.decrypt(dek_nonce, wrapped_dek, dek_aad)
    except InvalidTag as e:
        raise EnvelopeTamperError(
            "Cannot rewrap: existing wrapped DEK failed authentication."
        ) from e

    # 2. Re-wrap DEK with target master key
    new_master_key = mk_provider.get_key(target_key_id)
    new_dek_nonce = os.urandom(12)
    new_master_aesgcm = AESGCM(new_master_key)
    new_dek_aad = f"dek:{envelope.document_id}:{target_key_id}".encode()
    new_wrapped_dek = new_master_aesgcm.encrypt(new_dek_nonce, dek, new_dek_aad)

    # Return new envelope with updated master key wrapping
    return EncryptedDocumentEnvelope(
        version=envelope.version,
        document_id=envelope.document_id,
        master_key_id=target_key_id,
        dek_nonce_b64=base64.b64encode(new_dek_nonce).decode("ascii"),
        wrapped_dek_b64=base64.b64encode(new_wrapped_dek).decode("ascii"),
        doc_nonce_b64=envelope.doc_nonce_b64,
        doc_ciphertext_b64=envelope.doc_ciphertext_b64,
        plaintext_sha256=envelope.plaintext_sha256,
        created_at=envelope.created_at,
    )
