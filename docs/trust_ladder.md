# Trust Ladder Specification

Nirikshan enforces an ordinal evidential trust ladder to evaluate documents presented during scrutiny.

## The Ordinal Ladder

```
[Level 1: CRYPTOGRAPHIC]
  ▲ Digital Signatures (PKI / X.509, CMS/CAdES/PAdES)
  ▲ Signed QR payloads (cryptographically validated public keys)
  ▲ Immutable audit hashes
  │
[Level 2: ISSUER]
  ▲ Direct authority signatures (Municipal Corporation, Town Planning Authority)
  ▲ Verified government issuing bodies
  │
[Level 3: RECORD]
  ▲ Registered Sale Deeds, Gift Deeds, Sub-Registrar Book-1 records
  ▲ Record of Rights (RoR), Official Survey Settlements
  │
[Level 4: RULE]
  ▲ Deterministic compliance calculations (Built-up Area, FSR, Cadre Ratios)
  ▲ Evaluated strictly over verified Level 1–3 parameters
  │
[Level 5: STRUCTURAL / FORENSIC]
  ▲ PDF metadata consistency (Creation vs Mod date, producer mismatch)
  ▲ Font stream tampering, incremental update inspection
  ▲ Error Level Analysis (ELA) on stamped seals
  │
[Level 6: MODEL - ADVISORY ONLY]
  ▲ OCR text extraction, layout analysis, vision models
  ▲ CANNOT be the sole basis of a PASS or FAIL decision
  ▲ Must be corroborated or marked as ADVISORY
  │
[Level 0: UNVERIFIED CLAIM]
  ▼ Applicant Self-Attestation (Affidavits, self-declarations)
  ▼ NEVER counts as verified evidence for regulatory compliance
```

## Downgrade Rules
1. If forensic analysis indicates PDF tampering or inconsistent creation timestamps, higher-level trust can be downgraded to `FLAGGED_FOR_AUDIT`.
2. Any document without independent issuer or registry backing defaults to `UNVERIFIED_CLAIM`.
