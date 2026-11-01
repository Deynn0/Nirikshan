# Nirikshan Synthetic Benchmark Scrutiny Evaluation Report

- **Evaluation Timestamp**: 2026-10-31T19:29:14.641876+00:00
- **Total Benchmark Applications**: 24
- **Dev Split Applications**: 12 (Seed 42)
- **Held-Out Blind Applications**: 12 (Seed 1337)

## Executive Summary

| Evaluation Split | Total Apps | Clean Cases | False Alarm Rate | Macro Precision | Macro Recall | Macro F1 | Runtime (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dev (Calibration)** | 12 | 2 | 0.0% | 1.000 | 1.000 | **1.000** | 8.13s |
| **Blind (Held-Out)** | 12 | 2 | 0.0% | 1.000 | 1.000 | **1.000** | 7.36s |

## Held-Out Blind Split Performance (Developer Untuned)

| Planted Fraud Category | TP | FP | FN | TN | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `expired_certificate` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `edited_date_incremental_revision` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `font_mismatch` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `whiteout` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `invalid_or_applicant_signature` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `tampered_qr` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `duplicate_faculty_ids` | 2 | 0 | 0 | 10 | 1.000 | 1.000 | **1.000** |
| `reused_seal_and_lab_photo` | 2 | 0 | 0 | 10 | 1.000 | 1.000 | **1.000** |
| `geotag_outside_campus` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `scanned_hindi_documents` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |

## Dev Split Performance (Calibration Set)

| Planted Fraud Category | TP | FP | FN | TN | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `expired_certificate` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `edited_date_incremental_revision` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `font_mismatch` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `whiteout` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `invalid_or_applicant_signature` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `tampered_qr` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `duplicate_faculty_ids` | 2 | 0 | 0 | 10 | 1.000 | 1.000 | **1.000** |
| `reused_seal_and_lab_photo` | 2 | 0 | 0 | 10 | 1.000 | 1.000 | **1.000** |
| `geotag_outside_campus` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |
| `scanned_hindi_documents` | 1 | 0 | 0 | 11 | 1.000 | 1.000 | **1.000** |

## Scrutiny Failures & Root Cause Analysis

✅ **Zero Failures**: All 10 planted fraud patterns were successfully flagged with 100% precision and recall across both the development and held-out blind splits. Clean control sets produced 0.0% false alarm rate.

## Verification Pipeline Methodology

1. **Forensic Scan**: Analyzes structural anomalies, excessive font diversity via FontTools extraction, OpenCV whiteout concealment detection, and appended incremental update byte streams.
2. **Cryptographic Validation**: Verifies pyHanko digital signatures against the Root CA and enforces authorized `ISSUER_OFFICER` roles over `APPLICANT` self-attestation claims.
3. **Physical & Geofence Audit**: Extracts EXIF coordinates and runs Shapely polygon containment checks against declared campus boundaries.
4. **Signed QR Verification**: Validates Ed25519 Segno QR payloads with public keys from the official trusted registry.
5. **Cross-Application Graph**: Detects ghost faculty across institutions using salted HMAC-SHA256 privacy-preserving matching, photo perceptual hashing, and seal reuse detection.
