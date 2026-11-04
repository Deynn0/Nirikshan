"""Digital Forensics & Document Integrity: Image EXIF, photo tampering, C2PA provenance manifests."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import ExifTags, Image
from shapely.geometry import Polygon

from nirikshan.crypto.photo_integrity import validate_c2pa, verify_photo_integrity
from nirikshan.trust.ladder import TrustLevel


def _create_test_photo(
    lat_dms: tuple[float, float, float] | None = None,
    lon_dms: tuple[float, float, float] | None = None,
    software: str | None = None,
    make: str = "Samsung",
    model: str = "Galaxy S23",
    strip_exif: bool = False,
) -> bytes:
    img = Image.new("RGB", (200, 200), color=(120, 150, 180))
    buf = io.BytesIO()

    if strip_exif:
        img.save(buf, format="JPEG")
        return buf.getvalue()

    exif = img.getexif()
    if make:
        exif[ExifTags.Base.Make] = make
    if model:
        exif[ExifTags.Base.Model] = model
    if software:
        exif[ExifTags.Base.Software] = software
    exif[ExifTags.Base.DateTimeOriginal] = "2024:10:15 11:30:00"
    exif[ExifTags.Base.DateTime] = "2024:10:15 11:30:00"

    if lat_dms and lon_dms:
        gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
        gps_ifd[ExifTags.GPS.GPSLatitude] = lat_dms
        gps_ifd[ExifTags.GPS.GPSLatitudeRef] = "N"
        gps_ifd[ExifTags.GPS.GPSLongitude] = lon_dms
        gps_ifd[ExifTags.GPS.GPSLongitudeRef] = "E"

    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


@pytest.fixture
def campus_boundary() -> Polygon:
    return Polygon([
        (77.5900, 12.9700),
        (77.6000, 12.9700),
        (77.6000, 12.9800),
        (77.5900, 12.9800),
    ])


def test_photo_integrity_geofence_inside(campus_boundary: Polygon) -> None:
    photo_bytes = _create_test_photo(
        lat_dms=(12.0, 58.0, 30.0),
        lon_dms=(77.0, 35.0, 42.0),
    )
    report = verify_photo_integrity(
        photo_bytes,
        campus_polygon=campus_boundary,
        source_document_name="Engineering_Block_Photo.jpg",
    )
    assert report.is_tampered is False
    assert report.geofence.checked is True
    assert report.geofence.is_inside is True
    assert report.assessed_trust_level == TrustLevel.RECORD
    assert report.evidence_item.effective_trust_level() == TrustLevel.RECORD


def test_photo_integrity_geofence_outside_violation(campus_boundary: Polygon) -> None:
    photo_bytes = _create_test_photo(
        lat_dms=(13.0, 0.0, 36.0),
        lon_dms=(77.0, 39.0, 0.0),
    )
    report = verify_photo_integrity(
        photo_bytes,
        campus_polygon=campus_boundary,
        source_document_name="Offsite_Photo.jpg",
    )
    assert report.geofence.checked is True
    assert report.geofence.is_inside is False
    assert report.is_tampered is True
    assert report.geofence.distance_meters > 1000
    assert report.assessed_trust_level == TrustLevel.STRUCTURAL_FORENSIC


def test_photo_integrity_metadata_stripping_and_photoshop_detection() -> None:
    stripped_bytes = _create_test_photo(strip_exif=True)
    report_stripped = verify_photo_integrity(stripped_bytes)
    assert report_stripped.exif.is_stripped is True
    assert any("stripped" in f.lower() for f in report_stripped.tamper_flags)

    ps_bytes = _create_test_photo(
        lat_dms=(12.0, 58.0, 30.0),
        lon_dms=(77.0, 35.0, 42.0),
        software="Adobe Photoshop 2024 (Windows)",
    )
    report_ps = verify_photo_integrity(ps_bytes)
    assert report_ps.is_tampered is True
    assert any("photoshop" in f.lower() for f in report_ps.tamper_flags)
    assert report_ps.assessed_trust_level == TrustLevel.STRUCTURAL_FORENSIC


def test_c2pa_reader_graceful_handling() -> None:
    plain_photo = _create_test_photo(lat_dms=(12.0, 58.0, 30.0), lon_dms=(77.0, 35.0, 42.0))
    res = validate_c2pa(plain_photo)
    assert res.has_manifest is False
    assert "no c2pa manifest" in res.details.lower() or "not found" in res.details.lower()

