"""Photo physical and metadata integrity verification module.

Features:
- EXIF metadata extraction: timestamps (DateTimeOriginal, DateTime), GPS coordinates, device info.
- c2pa-python Content Authenticity manifest validation.
- Metadata stripping and inconsistency detection (missing EXIF, editing software tags, timestamp anomalies).
- Geofence verification against declared campus boundary polygon using Shapely.
- Maps verification findings into EvidenceItem adhering to Trust Ladder rules.
"""

from __future__ import annotations

import io
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from PIL import ExifTags, Image
from shapely.geometry import Point, Polygon

from nirikshan.trust.ladder import EvidenceItem, TrustLevel

log = logging.getLogger(__name__)

# Known photo editing and manipulation software strings
SUSPICIOUS_EDITING_SOFTWARE = [
    "photoshop",
    "gimp",
    "canva",
    "lightroom",
    "snapseed",
    "picsart",
    "vsco",
    "affinity photo",
    "coreldraw",
    "paint.net",
    "adobe premiere",
    "pixelmator",
]


@dataclass
class ExifData:
    """Extracted EXIF metadata."""

    has_exif: bool = False
    make: str | None = None
    model: str | None = None
    software: str | None = None
    datetime_original: datetime | None = None
    datetime_modified: datetime | None = None
    datetime_digitized: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    is_stripped: bool = False
    raw_tags: dict[str, Any] = field(default_factory=dict)


@dataclass
class C2paValidationResult:
    """Result of C2PA manifest inspection."""

    has_manifest: bool = False
    is_valid: bool = False
    title: str | None = None
    claim_generator: str | None = None
    issuer: str | None = None
    validation_status: list[dict[str, Any]] = field(default_factory=list)
    raw_manifest: dict[str, Any] | None = None
    details: str = ""


@dataclass
class GeofenceResult:
    """Result of geofence check against declared campus boundary."""

    checked: bool = False
    is_inside: bool = False
    distance_meters: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    details: str = ""


@dataclass
class PhotoIntegrityReport:
    """Consolidated physical and metadata integrity report for a photo."""

    file_name: str
    exif: ExifData
    c2pa: C2paValidationResult
    geofence: GeofenceResult
    is_tampered: bool = False
    tamper_flags: list[str] = field(default_factory=list)
    assessed_trust_level: TrustLevel = TrustLevel.STRUCTURAL_FORENSIC
    evidence_item: EvidenceItem | None = None
    summary: str = ""


def _parse_dms(dms_values: Any, ref: str) -> float | None:
    """Convert degrees, minutes, seconds tuple/list to signed decimal degrees."""
    try:
        if not dms_values or len(dms_values) < 3:
            return None
        deg = float(dms_values[0])
        minutes = float(dms_values[1])
        sec = float(dms_values[2])
        dec = deg + (minutes / 60.0) + (sec / 3600.0)
        if ref.upper() in ("S", "W"):
            dec = -dec
        return dec
    except Exception:
        return None


def _parse_exif_date(date_str: Any) -> datetime | None:
    """Parse EXIF date string format 'YYYY:MM:DD HH:MM:SS'."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        clean = date_str.strip()
        # Replace first two colons with dashes for standard ISO parsing if needed
        parts = clean.split(" ")
        if len(parts) == 2:
            d_part = parts[0].replace(":", "-")
            t_part = parts[1]
            return datetime.fromisoformat(f"{d_part}T{t_part}").replace(tzinfo=UTC)
    except Exception:
        pass
    return None


def extract_exif(image_bytes: bytes) -> ExifData:
    """Extract and parse EXIF tags from raw image bytes."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        raw_exif = img.getexif()
    except Exception as exc:
        log.warning("Could not read image EXIF: %s", exc)
        return ExifData(has_exif=False, is_stripped=True)

    if not raw_exif:
        return ExifData(has_exif=False, is_stripped=True)

    # Decode standard IFD tags
    tag_map: dict[str, Any] = {}
    for tag_id, val in raw_exif.items():
        name = ExifTags.TAGS.get(tag_id, str(tag_id))
        tag_map[name] = val

    # Decode GPS IFD if present
    lat = None
    lon = None
    alt = None
    try:
        gps_ifd = raw_exif.get_ifd(ExifTags.IFD.GPSInfo)
        if gps_ifd:
            lat_tuple = gps_ifd.get(ExifTags.GPS.GPSLatitude)
            lat_ref = gps_ifd.get(ExifTags.GPS.GPSLatitudeRef, "N")
            lon_tuple = gps_ifd.get(ExifTags.GPS.GPSLongitude)
            lon_ref = gps_ifd.get(ExifTags.GPS.GPSLongitudeRef, "E")
            alt_val = gps_ifd.get(ExifTags.GPS.GPSAltitude)

            if lat_tuple:
                lat = _parse_dms(lat_tuple, str(lat_ref))
            if lon_tuple:
                lon = _parse_dms(lon_tuple, str(lon_ref))
            if alt_val is not None:
                import contextlib
                with contextlib.suppress(Exception):
                    alt = float(alt_val)
    except Exception as e:
        log.debug("GPS IFD parse error: %s", e)

    # Dates
    dt_orig = _parse_exif_date(tag_map.get("DateTimeOriginal"))
    dt_mod = _parse_exif_date(tag_map.get("DateTime"))
    dt_dig = _parse_exif_date(tag_map.get("DateTimeDigitized"))

    # Device
    make = str(tag_map.get("Make")).strip() if tag_map.get("Make") else None
    model = str(tag_map.get("Model")).strip() if tag_map.get("Model") else None
    software = str(tag_map.get("Software")).strip() if tag_map.get("Software") else None

    # Determine if stripped: If camera image has 0 device or timestamp metadata
    is_stripped = not bool(make or model or dt_orig or lat)

    return ExifData(
        has_exif=True,
        make=make,
        model=model,
        software=software,
        datetime_original=dt_orig,
        datetime_modified=dt_mod,
        datetime_digitized=dt_dig,
        latitude=lat,
        longitude=lon,
        altitude=alt,
        is_stripped=is_stripped,
        raw_tags={str(k): str(v) for k, v in tag_map.items()},
    )


def validate_c2pa(image_bytes: bytes, mime_type: str = "image/jpeg") -> C2paValidationResult:
    """Inspect and validate C2PA Content Authenticity manifest."""
    try:
        import c2pa
    except ImportError:
        return C2paValidationResult(
            has_manifest=False,
            details="c2pa-python is not installed in the current environment.",
        )

    stream = io.BytesIO(image_bytes)
    try:
        with c2pa.Reader(mime_type, stream) as reader:
            manifest_json = reader.json()
            manifest_data = json.loads(manifest_json)

            # Active manifest
            active_label = manifest_data.get("active_manifest")
            manifests = manifest_data.get("manifests", {})
            active_m = manifests.get(active_label, {}) if active_label else {}

            title = active_m.get("title")
            claim_gen = active_m.get("claim_generator")
            signature_info = active_m.get("signature_info", {})
            issuer = signature_info.get("issuer")

            validation_status = manifest_data.get("validation_status", [])
            # If validation_status is empty or all codes are OK, valid
            is_valid = True
            if validation_status:
                for entry in validation_status:
                    code = entry.get("code", "")
                    if "error" in code.lower() or "fail" in code.lower() or "invalid" in code.lower():
                        is_valid = False
                        break

            return C2paValidationResult(
                has_manifest=True,
                is_valid=is_valid,
                title=title,
                claim_generator=claim_gen,
                issuer=issuer,
                validation_status=validation_status,
                raw_manifest=manifest_data,
                details=f"C2PA manifest found: '{title}' by '{issuer}' (valid: {is_valid}).",
            )
    except Exception as exc:
        # Expected ManifestNotFound for standard camera photos
        err_name = type(exc).__name__
        if "ManifestNotFound" in err_name or "no JUMBF" in str(exc):
            return C2paValidationResult(
                has_manifest=False,
                details="No C2PA manifest found in image stream.",
            )
        log.warning("C2PA inspection anomaly: %s", exc)
        return C2paValidationResult(
            has_manifest=False,
            is_valid=False,
            details=f"C2PA reader error: {exc}",
        )


def check_geofence(
    lat: float | None,
    lon: float | None,
    campus_polygon: Polygon | list[tuple[float, float]] | None,
) -> GeofenceResult:
    """Verify if photo coordinate falls inside declared campus boundary polygon."""
    if lat is None or lon is None:
        return GeofenceResult(
            checked=False,
            is_inside=False,
            details="No GPS coordinates present in photo EXIF.",
        )

    if campus_polygon is None:
        return GeofenceResult(
            checked=False,
            latitude=lat,
            longitude=lon,
            details="No declared campus polygon provided for geofence validation.",
        )

    # Build polygon
    if isinstance(campus_polygon, list):
        # Auto-detect if coordinates are (lon, lat) or (lat, lon)
        # Indian longitude is 68°E to 97°E, latitude is 8°N to 37°N
        first = campus_polygon[0]
        if first[0] < first[1] and 8.0 <= first[0] <= 38.0 and 68.0 <= first[1] <= 98.0:
            # Format was (lat, lon) -> convert to (lon, lat)
            pts = [(p[1], p[0]) for p in campus_polygon]
        else:
            pts = campus_polygon
        poly = Polygon(pts)
    else:
        poly = campus_polygon

    pt = Point(lon, lat)
    is_inside = poly.contains(pt) or poly.touches(pt)

    # Approximate distance in meters if outside (1 deg ~ 111,000 m)
    dist_m = None
    if not is_inside:
        dist_deg = pt.distance(poly)
        dist_m = round(dist_deg * 111319.5, 2)
        details = (
            f"Geofence VIOLATION: Photo coordinates ({lat:.6f}, {lon:.6f}) are "
            f"outside campus boundary by approx {dist_m} meters."
        )
    else:
        dist_m = 0.0
        details = f"Geofence PASS: Photo coordinates ({lat:.6f}, {lon:.6f}) fall inside campus polygon."

    return GeofenceResult(
        checked=True,
        is_inside=is_inside,
        distance_meters=dist_m,
        latitude=lat,
        longitude=lon,
        details=details,
    )


def verify_photo_integrity(
    image_input: bytes | Path | io.BytesIO,
    campus_polygon: Polygon | list[tuple[float, float]] | None = None,
    *,
    expected_capture_window: tuple[datetime, datetime] | None = None,
    source_document_id: str = "photo_unknown",
    source_document_name: str = "site_photo.jpg",
    mime_type: str = "image/jpeg",
) -> PhotoIntegrityReport:
    """Analyze photo integrity: EXIF extraction, C2PA validation, and geofencing.

    Trust Ladder mapping:
    - Valid C2PA + Geofence Pass: TrustLevel.CRYPTOGRAPHIC (Rank 60)
    - Camera EXIF + Geofence Pass (no C2PA): TrustLevel.RECORD (Rank 40)
    - Metadata stripped / Editing software detected / Geofence violated:
      TrustLevel.STRUCTURAL_FORENSIC (Rank 20) with is_tampered = True
    """
    if isinstance(image_input, (str, Path)):
        img_bytes = Path(image_input).read_bytes()
        file_name = Path(image_input).name
    elif isinstance(image_input, io.BytesIO):
        img_bytes = image_input.getvalue()
        file_name = source_document_name
    else:
        img_bytes = image_input
        file_name = source_document_name

    # 1. EXIF extraction
    exif = extract_exif(img_bytes)

    # 2. C2PA validation
    c2pa_res = validate_c2pa(img_bytes, mime_type=mime_type)

    # 3. Geofence check
    geofence_res = check_geofence(exif.latitude, exif.longitude, campus_polygon)

    tamper_flags: list[str] = []
    is_tampered = False

    # Check for metadata stripping
    if exif.is_stripped:
        tamper_flags.append("EXIF metadata has been completely stripped or sanitized.")

    # Check for photo editing tools
    if exif.software:
        soft_lower = exif.software.lower()
        for s in SUSPICIOUS_EDITING_SOFTWARE:
            if s in soft_lower:
                is_tampered = True
                tamper_flags.append(
                    f"Photo manipulation software detected in EXIF header: '{exif.software}'"
                )
                break

    # Check timestamp inconsistencies
    if exif.datetime_original and exif.datetime_modified:
        diff_sec = (exif.datetime_modified - exif.datetime_original).total_seconds()
        if diff_sec > 86400:  # modified more than 24h after original
            tamper_flags.append(
                f"Timestamp inconsistency: Modified date ({exif.datetime_modified}) differs significantly from capture date ({exif.datetime_original})."
            )

    # Check capture window
    if expected_capture_window and exif.datetime_original:
        start_w, end_w = expected_capture_window
        if not (start_w <= exif.datetime_original <= end_w):
            tamper_flags.append(
                f"Capture timestamp ({exif.datetime_original}) outside expected window ({start_w} to {end_w})."
            )

    # Check geofence violation
    if geofence_res.checked and not geofence_res.is_inside:
        is_tampered = True
        tamper_flags.append(geofence_res.details)

    # Check C2PA tampering
    if c2pa_res.has_manifest and not c2pa_res.is_valid:
        is_tampered = True
        tamper_flags.append(f"C2PA manifest signature or assertion verification failed: {c2pa_res.details}")

    # Determine Trust Ladder level
    if is_tampered or (geofence_res.checked and not geofence_res.is_inside):
        assessed_trust = TrustLevel.STRUCTURAL_FORENSIC
    elif c2pa_res.has_manifest and c2pa_res.is_valid and (not geofence_res.checked or geofence_res.is_inside):
        assessed_trust = TrustLevel.CRYPTOGRAPHIC
    elif exif.has_exif and not exif.is_stripped and (not geofence_res.checked or geofence_res.is_inside):
        assessed_trust = TrustLevel.RECORD
    else:
        assessed_trust = TrustLevel.STRUCTURAL_FORENSIC

    ev_id = f"ev-photo-{uuid4().hex[:6]}"
    evidence = EvidenceItem(
        evidence_id=ev_id,
        trust_level=assessed_trust,
        source_type="Site Inspection Photo",
        description=(
            f"Photo integrity analysis for {file_name}. "
            f"GPS: ({exif.latitude}, {exif.longitude}). "
            f"Geofence: {'PASS' if geofence_res.is_inside else 'FAIL' if geofence_res.checked else 'UNCHECKED'}. "
            f"C2PA: {'VALID' if c2pa_res.is_valid else 'ABSENT' if not c2pa_res.has_manifest else 'INVALID'}. "
            f"Tamper flags: {len(tamper_flags)}."
        ),
        raw_value={
            "file_name": file_name,
            "has_exif": exif.has_exif,
            "device": f"{exif.make or ''} {exif.model or ''}".strip(),
            "software": exif.software,
            "timestamp": str(exif.datetime_original),
            "latitude": exif.latitude,
            "longitude": exif.longitude,
            "geofence_pass": geofence_res.is_inside if geofence_res.checked else None,
            "c2pa_present": c2pa_res.has_manifest,
            "c2pa_valid": c2pa_res.is_valid,
            "tamper_flags": tamper_flags,
            "is_tampered": is_tampered,
        },
        source_document_id=source_document_id,
        source_document_name=source_document_name,
        is_self_attested=False,
        is_tampered=is_tampered,
        verification_method="EXIF_C2PA_SHAPELY_GEOFENCE",
    )

    summary = (
        f"Photo {file_name}: Trust={assessed_trust.value}. "
        f"Tampered={is_tampered}. "
        f"GPS=({exif.latitude}, {exif.longitude}). "
        f"Flags={tamper_flags}."
    )

    return PhotoIntegrityReport(
        file_name=file_name,
        exif=exif,
        c2pa=c2pa_res,
        geofence=geofence_res,
        is_tampered=is_tampered,
        tamper_flags=tamper_flags,
        assessed_trust_level=assessed_trust,
        evidence_item=evidence,
        summary=summary,
    )
