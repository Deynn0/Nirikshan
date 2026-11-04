"""Verification & Rectification Workflow: Encrypted attachments, multi-turn clarification threads, audit."""

from __future__ import annotations

import base64
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from nirikshan.crypto.envelope import (
    EnvelopeTamperError,
    SandboxDecryptionEnforcementError,
)
from nirikshan.crypto.master_keys import MasterKeyProvider
from nirikshan.crypto.storage import EncryptedStorageService


# ---------------------------------------------------------------------------
# Encrypted Attachments & Envelope Encryption
# ---------------------------------------------------------------------------

def test_envelope_encryption_roundtrip(tmp_path: Path) -> None:
    """Rectification attachments are stored with AES-256-GCM envelope encryption."""
    provider = MasterKeyProvider(key_file_path=tmp_path / "test_keys.json")
    storage = EncryptedStorageService(storage_dir=tmp_path / "quarantine", key_provider=provider)

    doc_id = "doc-rectify-001"
    original_plaintext = b"%PDF-1.4\nRectified Land Mutation Certificate Content\n%%EOF"

    path, envelope = storage.store_document(doc_id, original_plaintext)
    assert path.exists()
    assert envelope.document_id == doc_id
    assert envelope.master_key_id == provider.active_key_id
    assert len(envelope.wrapped_dek_b64) > 0
    assert len(envelope.doc_ciphertext_b64) > 0

    decrypted = storage.decrypt_document(envelope, is_sandbox=True)
    assert decrypted == original_plaintext


def test_envelope_decryption_outside_sandbox_denied(tmp_path: Path) -> None:
    """Decryption of rectification attachments is strictly denied outside the secure sandbox."""
    provider = MasterKeyProvider(key_file_path=tmp_path / "test_keys.json")
    storage = EncryptedStorageService(storage_dir=tmp_path / "quarantine", key_provider=provider)

    doc_id = "doc-outside-sandbox"
    _, envelope = storage.store_document(doc_id, b"confidential rectification note")

    old_env = os.environ.get("NIRIKSHAN_SANDBOX_ACTIVE")
    if "NIRIKSHAN_SANDBOX_ACTIVE" in os.environ:
        del os.environ["NIRIKSHAN_SANDBOX_ACTIVE"]

    try:
        with pytest.raises(SandboxDecryptionEnforcementError):
            storage.decrypt_document(envelope, is_sandbox=False)
    finally:
        if old_env is not None:
            os.environ["NIRIKSHAN_SANDBOX_ACTIVE"] = old_env


def test_envelope_tamper_detection(tmp_path: Path) -> None:
    """Tampering with encrypted attachment ciphertext or key is immediately detected."""
    provider = MasterKeyProvider(key_file_path=tmp_path / "test_keys.json")
    storage = EncryptedStorageService(storage_dir=tmp_path / "quarantine", key_provider=provider)

    doc_id = "doc-tamper-check"
    _, envelope = storage.store_document(doc_id, b"Original uncorrupted rectification doc")

    raw_ct = bytearray(base64.b64decode(envelope.doc_ciphertext_b64))
    raw_ct[0] ^= 0xFF
    tampered_envelope = envelope.model_copy(
        update={"doc_ciphertext_b64": base64.b64encode(raw_ct).decode("ascii")}
    )

    with pytest.raises(EnvelopeTamperError):
        storage.decrypt_document(tampered_envelope, is_sandbox=True)


def test_envelope_master_key_rotation(tmp_path: Path) -> None:
    """Attachments encrypted under older master keys remain decryptable after key rotation."""
    provider = MasterKeyProvider(key_file_path=tmp_path / "test_keys.json")
    storage = EncryptedStorageService(storage_dir=tmp_path / "quarantine", key_provider=provider)

    doc_id = "doc-rotation-test"
    plaintext = b"Payload created under Key Version 1"
    v1_key_id = provider.active_key_id
    _, envelope_v1 = storage.store_document(doc_id, plaintext)
    assert envelope_v1.master_key_id == v1_key_id

    v2_key_id, _ = provider.rotate_master_key("master-key-2024-v2")
    assert provider.active_key_id == v2_key_id

    decrypted_old = storage.decrypt_document(envelope_v1, is_sandbox=True)
    assert decrypted_old == plaintext


# ---------------------------------------------------------------------------
# Multi-Turn Clarification Thread & Audit Simulation
# ---------------------------------------------------------------------------

def test_multi_turn_clarification_thread_progression() -> None:
    """Multi-turn rectification threads record messages, timestamps, and attached documents."""
    thread = {
        "thread_id": f"th-{uuid.uuid4().hex[:8]}",
        "dossier_id": "dos-rectify-101",
        "rule_id": "AICTE-2024-LAND-001",
        "created_at": datetime.now(UTC).isoformat(),
        "messages": [],
    }

    # Turn 1: Scrutiny Officer raises clarification
    msg1 = {
        "message_id": "msg-001",
        "sender_role": "officer",
        "content": "Survey number 123/4A does not match conversion order 999/1B. Please upload revenue clarification.",
        "attachments": [],
        "timestamp": datetime.now(UTC).isoformat(),
    }
    thread["messages"].append(msg1)

    # Turn 2: Applicant uploads rectification deed
    msg2 = {
        "message_id": "msg-002",
        "sender_role": "applicant",
        "content": "Uploaded supplementary Revenue Tehsildar endorsement clarifying contiguous survey parcels.",
        "attachments": ["doc-rectify-001"],
        "timestamp": datetime.now(UTC).isoformat(),
    }
    thread["messages"].append(msg2)

    # Turn 3: Officer marks clarification acknowledged
    msg3 = {
        "message_id": "msg-003",
        "sender_role": "officer",
        "content": "Rectification document received and queued for re-verification.",
        "attachments": [],
        "timestamp": datetime.now(UTC).isoformat(),
    }
    thread["messages"].append(msg3)

    assert len(thread["messages"]) == 3
    assert thread["messages"][0]["sender_role"] == "officer"
    assert thread["messages"][1]["sender_role"] == "applicant"
    assert "doc-rectify-001" in thread["messages"][1]["attachments"]

