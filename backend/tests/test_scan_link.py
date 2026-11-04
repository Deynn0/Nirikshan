"""Digital Forensics & Document Integrity: Signed QR verification, link tokens, upscaled QR fallbacks."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import qrcode
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from httpx import ASGITransport, AsyncClient

from nirikshan.crypto.qr_verifier import (
    Keyring,
    KeyringEntry,
    QRVerificationStatus,
    decode_qr_from_image,
    sign_qr_payload,
    verify_qr_payload,
)
from nirikshan.main import app
from nirikshan.trust.ladder import TrustLevel


@pytest.fixture(scope="module")
def qr_keyring() -> dict:
    ed_priv = ed25519.Ed25519PrivateKey.generate()
    ed_pub_pem = ed_priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    ec_priv = ec.generate_private_key(ec.SECP256R1())
    ec_pub_pem = ec_priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    kr = Keyring()
    kr.add_key(
        KeyringEntry(
            key_id="test-aicte-ed25519",
            algorithm="Ed25519",
            issuer="All India Council for Technical Education",
            role="ISSUER_OFFICER",
            public_key_pem=ed_pub_pem,
            public_key_obj=ed_priv.public_key(),
        )
    )
    kr.add_key(
        KeyringEntry(
            key_id="test-fire-ecdsa",
            algorithm="ECDSA",
            curve="SECP256R1",
            issuer="Department of Fire & Emergency Services",
            role="ISSUER_OFFICER",
            public_key_pem=ec_pub_pem,
            public_key_obj=ec_priv.public_key(),
        )
    )
    return {
        "keyring": kr,
        "ed_priv": ed_priv,
        "ec_priv": ec_priv,
    }


def test_qr_verification_roundtrip_ed25519(qr_keyring: dict) -> None:
    kr = qr_keyring["keyring"]
    ed_priv = qr_keyring["ed_priv"]

    doc_data = {
        "noc_number": "AICTE-2024-NOC-4921",
        "institution": "Apex Engineering Institute",
        "valid_until": "2027-03-31",
        "approved_intake": 420,
    }
    payload = sign_qr_payload(doc_data, ed_priv, key_id="test-aicte-ed25519")

    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(json.dumps(payload))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")

    decoded_texts = decode_qr_from_image(buf.getvalue())
    assert len(decoded_texts) == 1

    res = verify_qr_payload(decoded_texts[0], keyring=kr)
    assert res.status == QRVerificationStatus.VALID
    assert res.is_tampered is False
    assert res.key_id == "test-aicte-ed25519"
    assert res.evidence_item.effective_trust_level() == TrustLevel.CRYPTOGRAPHIC


def test_qr_verification_roundtrip_ecdsa(qr_keyring: dict) -> None:
    kr = qr_keyring["keyring"]
    ec_priv = qr_keyring["ec_priv"]

    data = {"permit_id": "FIRE-NOC-2024-88", "status": "APPROVED"}
    payload = sign_qr_payload(data, ec_priv, key_id="test-fire-ecdsa")

    res = verify_qr_payload(payload, keyring=kr)
    assert res.status == QRVerificationStatus.VALID
    assert res.is_tampered is False
    assert res.evidence_item.effective_trust_level() == TrustLevel.CRYPTOGRAPHIC


def test_qr_verification_tampered_payload(qr_keyring: dict) -> None:
    kr = qr_keyring["keyring"]
    ed_priv = qr_keyring["ed_priv"]

    data = {"intake": 300}
    payload = sign_qr_payload(data, ed_priv, key_id="test-aicte-ed25519")
    payload["data"]["intake"] = 9000

    res = verify_qr_payload(payload, keyring=kr)
    assert res.status == QRVerificationStatus.INVALID
    assert res.is_tampered is True
    assert res.evidence_item.effective_trust_level() == TrustLevel.STRUCTURAL_FORENSIC


def test_qr_verification_unknown_issuer(qr_keyring: dict) -> None:
    kr = qr_keyring["keyring"]
    ed_priv = qr_keyring["ed_priv"]

    payload = sign_qr_payload({"foo": "bar"}, ed_priv, key_id="unregistered-foreign-key")
    res = verify_qr_payload(payload, keyring=kr)
    assert res.status == QRVerificationStatus.UNKNOWN_ISSUER
    assert res.is_tampered is False


def test_upscaled_qr_fallback(qr_keyring: dict) -> None:
    payload = sign_qr_payload({"doc": "upscaled_test"}, qr_keyring["ed_priv"], key_id="test-aicte-ed25519")
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(json.dumps(payload))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # Simulate low-res upscale
    upscaled = img.resize((400, 400))
    buf = io.BytesIO()
    upscaled.save(buf, format="PNG")
    decoded = decode_qr_from_image(buf.getvalue())
    assert len(decoded) >= 1


@pytest.mark.asyncio
async def test_get_scan_endpoint_returns_mobile_viewport() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/scan")

    assert response.status_code == 200
    html = response.text
    assert '<meta name="viewport"' in html
    assert 'type="file"' in html
    assert 'accept="image/*"' in html


@pytest.mark.asyncio
async def test_post_scan_endpoint_image_upload(qr_keyring: dict) -> None:
    kr = qr_keyring["keyring"]
    ed_priv = qr_keyring["ed_priv"]

    payload = sign_qr_payload(
        {"approval_id": "AICTE-2024-APX-01", "status": "APPROVED"},
        ed_priv,
        key_id="test-aicte-ed25519",
    )
    qr_img = qrcode.make(json.dumps(payload))
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")

    with patch("nirikshan.api.routes_scan.Keyring", return_value=kr):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            files = {"file": ("qr_code.png", buf.getvalue(), "image/png")}
            response = await ac.post("/scan", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "VALID"
    assert data["trust_ladder_level"] == "CRYPTOGRAPHIC"


@pytest.mark.asyncio
async def test_post_scan_endpoint_invalid_and_unknown_issuer(qr_keyring: dict) -> None:
    kr = qr_keyring["keyring"]
    ed_priv = qr_keyring["ed_priv"]

    with patch("nirikshan.api.routes_scan.Keyring", return_value=kr):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            payload_unk = sign_qr_payload({"x": 1}, ed_priv, key_id="unknown-999")
            res_unk = await ac.post("/scan", json=payload_unk)
            assert res_unk.status_code == 200
            assert res_unk.json()["status"] == "UNKNOWN_ISSUER"

            payload_tampered = sign_qr_payload({"x": 1}, ed_priv, key_id="test-aicte-ed25519")
            payload_tampered["data"]["x"] = 999
            res_inv = await ac.post("/scan", json=payload_tampered)
            assert res_inv.status_code == 200
            assert res_inv.json()["status"] == "INVALID"
