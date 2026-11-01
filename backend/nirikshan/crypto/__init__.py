"""Cryptographic and physical integrity verification package."""

from nirikshan.crypto.pdf_verifier import (
    PdfVerificationReport,
    SignatureVerificationDetail,
    load_bundled_trust_roots,
    verify_pdf_signatures,
)
from nirikshan.crypto.photo_integrity import (
    C2paValidationResult,
    ExifData,
    GeofenceResult,
    PhotoIntegrityReport,
    check_geofence,
    extract_exif,
    validate_c2pa,
    verify_photo_integrity,
)
from nirikshan.crypto.qr_verifier import (
    Keyring,
    KeyringEntry,
    QRVerificationResult,
    QRVerificationStatus,
    canonicalize_data,
    decode_qr_from_image,
    sign_qr_payload,
    verify_qr_payload,
)
from nirikshan.crypto.signer_disambiguation import (
    ApplicantIdentity,
    IssuerEntry,
    IssuerRegistry,
    SignerDisambiguationResult,
    SignerRole,
    disambiguate_signer,
)

__all__ = [
    # Signer Disambiguation
    "SignerRole",
    "ApplicantIdentity",
    "IssuerEntry",
    "IssuerRegistry",
    "SignerDisambiguationResult",
    "disambiguate_signer",
    # PDF Signature Verification
    "PdfVerificationReport",
    "SignatureVerificationDetail",
    "verify_pdf_signatures",
    "load_bundled_trust_roots",
    # QR Verification
    "QRVerificationStatus",
    "KeyringEntry",
    "Keyring",
    "QRVerificationResult",
    "decode_qr_from_image",
    "verify_qr_payload",
    "sign_qr_payload",
    "canonicalize_data",
    # Photo Integrity
    "ExifData",
    "C2paValidationResult",
    "GeofenceResult",
    "PhotoIntegrityReport",
    "extract_exif",
    "validate_c2pa",
    "check_geofence",
    "verify_photo_integrity",
]
