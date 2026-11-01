"""Unit tests for synthetic benchmark fixtures generator and scrutiny evaluation pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import asn1crypto.x509 as asn1_x509
import pytest

from nirikshan.crypto.qr_verifier import Keyring
from scripts.evaluate import (
    evaluate_single_application,
    evaluate_split,
)
from scripts.make_fixtures import generate_fixtures


@pytest.fixture(scope="session")
def test_fixtures_dir(tmp_path_factory) -> Path:
    """Generate a test benchmark fixtures directory with 12 applications."""
    fixtures_dir = tmp_path_factory.mktemp("test_synthetic_fixtures")
    generate_fixtures(
        output_dir=fixtures_dir,
        num_apps=12,
        seed_dev=42,
        seed_blind=1337,
    )
    return fixtures_dir


def test_make_fixtures_generates_manifest_and_splits(test_fixtures_dir: Path) -> None:
    """Verify ground_truth.json contains valid manifest, crypto keys, and split metadata."""
    manifest_path = test_fixtures_dir / "ground_truth.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["total_applications"] == 12
    assert "dev" in manifest["splits"]
    assert "blind" in manifest["splits"]

    # Verify cryptographic material
    assert (test_fixtures_dir / "trust_ca.der").exists()
    assert (test_fixtures_dir / "trust_ca.pem").exists()
    assert (test_fixtures_dir / "keyring.json").exists()
    assert (test_fixtures_dir / "fonts" / "SyntheticMismatchFont.ttf").exists()

    # Check applications exist
    for app_id, meta in manifest["applications"].items():
        split = meta["split"]
        app_dir = test_fixtures_dir / split / app_id
        assert app_dir.exists()
        assert (app_dir / "meta.json").exists()
        assert (app_dir / "documents").exists()
        assert (app_dir / "photos").exists()


def test_evaluate_single_application_clean(test_fixtures_dir: Path) -> None:
    """Verify clean application yields zero detected fraud categories."""
    manifest_path = test_fixtures_dir / "ground_truth.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    ca_der = (test_fixtures_dir / "trust_ca.der").read_bytes()
    asn1_ca = asn1_x509.Certificate.load(ca_der)
    keyring = Keyring(test_fixtures_dir / "keyring.json")

    clean_app_id = "app_dev_01"
    app_meta = manifest["applications"][clean_app_id]
    app_dir = test_fixtures_dir / "dev" / clean_app_id

    detected, ev_logs = evaluate_single_application(app_meta, app_dir, asn1_ca, keyring)
    assert len(detected) == 0, f"Clean app was falsely flagged with: {detected}"


def test_evaluate_single_application_planted_frauds(test_fixtures_dir: Path) -> None:
    """Verify specific planted frauds are detected on individual applications."""
    manifest_path = test_fixtures_dir / "ground_truth.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    ca_der = (test_fixtures_dir / "trust_ca.der").read_bytes()
    asn1_ca = asn1_x509.Certificate.load(ca_der)
    keyring = Keyring(test_fixtures_dir / "keyring.json")

    # 1. Expired certificate
    app_03 = manifest["applications"]["app_dev_03"]
    det_03, _ = evaluate_single_application(app_03, test_fixtures_dir / "dev" / "app_dev_03", asn1_ca, keyring)
    assert "expired_certificate" in det_03

    # 2. Incremental revision
    app_04 = manifest["applications"]["app_dev_04"]
    det_04, _ = evaluate_single_application(app_04, test_fixtures_dir / "dev" / "app_dev_04", asn1_ca, keyring)
    assert "edited_date_incremental_revision" in det_04

    # 3. Font mismatch
    app_05 = manifest["applications"]["app_dev_05"]
    det_05, _ = evaluate_single_application(app_05, test_fixtures_dir / "dev" / "app_dev_05", asn1_ca, keyring)
    assert "font_mismatch" in det_05

    # 4. Whiteout
    app_06 = manifest["applications"]["app_dev_06"]
    det_06, _ = evaluate_single_application(app_06, test_fixtures_dir / "dev" / "app_dev_06", asn1_ca, keyring)
    assert "whiteout" in det_06

    # 5. Geotag outside campus
    if "app_dev_11" in manifest["applications"]:
        app_11 = manifest["applications"]["app_dev_11"]
        det_11, _ = evaluate_single_application(app_11, test_fixtures_dir / "dev" / "app_dev_11", asn1_ca, keyring)
        assert "geotag_outside_campus" in det_11


def test_evaluate_split_metrics_and_zero_clean_false_alarms(test_fixtures_dir: Path) -> None:
    """Verify evaluate_split computes precision, recall, F1, and clean false alarm rate."""
    manifest_path = test_fixtures_dir / "ground_truth.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    ca_der = (test_fixtures_dir / "trust_ca.der").read_bytes()
    asn1_ca = asn1_x509.Certificate.load(ca_der)
    keyring = Keyring(test_fixtures_dir / "keyring.json")

    dev_res = evaluate_split("dev", manifest, test_fixtures_dir, asn1_ca, keyring)
    assert dev_res.num_applications == 6
    assert dev_res.false_alarm_rate == 0.0
    assert dev_res.macro_f1 >= 0.90
    assert dev_res.total_runtime_seconds > 0.0
