# Nirikshan Trust Anchors & Indian CCA Root Certificates

This directory stores trusted public key infrastructure (PKI) roots, issuing authority registries, and public keyrings for offline cryptographic verification within the Nirikshan Regulatory Scrutiny System.

> **CRITICAL SECURITY NOTICE**: 
> **Never fabricate, simulate, or commit mock certificate files pretending to be official government roots.**
> Only genuine public certificates downloaded directly from the official Controller of Certifying Authorities (CCA) portal and cryptographically verified against published government gazette fingerprints should be placed in `backend/trust/roots/`.

---

## 1. Controller of Certifying Authorities (CCA) India Roots

Under the Indian Information Technology Act, 2000, all digital signatures recognized for legal purposes in India (such as municipal NOCs, land registry e-deeds, AICTE approvals, and corporate registrations) must chain to the **Root Certifying Authority of India (RCAI)** operated by the CCA.

### Root Certifying Authority of India (RCAI)
1. **RCAI 2014 Root Certificate**:
   - **Common Name (CN)**: `Root Certifying Authority of India 2014`
   - **Organization (O)**: `Controller of Certifying Authorities`
   - **Country (C)**: `IN`
   - **Signature Algorithm**: `sha256WithRSAEncryption` (2048-bit)
   - **Official CCA Download**: `https://cca.gov.in` (Repository -> RCAI 2014)

2. **RCAI 2022 Root Certificate**:
   - **Common Name (CN)**: `Root Certifying Authority of India 2022`
   - **Organization (O)**: `Controller of Certifying Authorities`
   - **Country (C)**: `IN`
   - **Signature Algorithm**: `sha384WithRSAEncryption` or `sha256WithRSAEncryption` (4096-bit)
   - **Official CCA Download**: `https://cca.gov.in` (Repository -> RCAI 2022)

---

## 2. Licensed Sub-CAs under CCA India

In India, end-user and institutional DSCs (Digital Signature Certificates) are issued by licensed Certifying Authorities (Sub-CAs) operating under RCAI:

| Certifying Authority | Issuer Common Name / Organization | Common Use Case |
| :--- | :--- | :--- |
| **eMudhra** | `eMudhra Sub-CA for Class 3 Individual / Org` | Municipal approvals, corporate filings |
| **(n)Code Solutions** | `(n)Code Solutions CA` | e-Procurement, government tenders |
| **Capricorn Identity Services** | `Capricorn Sub-CA Class 3` | Building sanctions, revenue deeds |
| **Verasys Technologies (Vsign)** | `Vsign Sub-CA Class 3` | Academic & regulatory certificates |
| **National Informatics Centre (NIC CA)** | `NIC Sub-CA` | Government officer & departmental signing |
| **CDAC CA** | `CDAC Sub-CA` | Institutional & research certifications |
| **Pantasign CA** | `Pantasign Sub-CA Class 3` | Professional engineer & architect NOCs |
| **IDsign CA** | `IDsign Sub-CA Class 3` | Land development endorsements |

---

## 3. How to Obtain and Verify Certificate Fingerprints

To install trusted roots into `backend/trust/roots/`:

1. **Download Official Root / Sub-CA**:
   Download the `.cer` or `.crt` certificate directly from:
   - Official CCA Portal: [https://cca.gov.in/root_certificates.html](https://cca.gov.in/root_certificates.html)
   - Respective licensed CA repository pages (e.g., `https://www.emudhra.com/repository`)

2. **Verify SHA-256 Fingerprint**:
   Before placing any root file into `backend/trust/roots/`, calculate its SHA-256 fingerprint:
   ```bash
   # On Linux/macOS
   openssl x509 -noout -fingerprint -sha256 -in <downloaded_cert>.cer

   # On Windows PowerShell
   Get-FileHash -Algorithm SHA256 .\<downloaded_cert>.cer
   ```
   Cross-reference the calculated fingerprint against the gazette notification published in the Official Gazette of India or the signed fingerprint table on `https://cca.gov.in`.

3. **Placement**:
   Place verified certificates (`.cer`, `.crt`, `.pem`) into:
   ```
   backend/trust/roots/
   ```
   Nirikshan's `pyHanko` verification engine loads all certificates in this directory as trust anchors for building PAdES/CMS validation chains.

---

## 4. Issuer Registry (`issuers.yaml`)

`backend/trust/issuers.yaml` maps public regulatory bodies and municipal authorities to their expected certificate subject parameters, organizations, and domain patterns. It disambiguates whether a signer is an `ISSUER_OFFICER`, the `APPLICANT`, or an `UNKNOWN` third party.

---

## 5. Public Keyring (`keyring.json`)

`backend/trust/keyring.json` holds trusted Ed25519 and ECDSA public keys for verifying QR codes embedded in institutional NOCs, land conversion orders, and building sanctioned plans.
