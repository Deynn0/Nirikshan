"""Generate test PDF fixtures using reportlab.

Produces:
  tests/fixtures/clean_doc.pdf        — normal 2-page doc
  tests/fixtures/tampered_js.pdf      — PDF with /JS token
  tests/fixtures/whiteout_page.pdf    — page with white rectangle
  tests/fixtures/multi_font.pdf       — page with many font families
  tests/fixtures/scanned_stub.pdf     — blank page (simulates scanned, no text)

Run: python tests/fixtures/generate_fixtures.py
"""

import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except ImportError:
    print("reportlab not installed — run: pip install reportlab", file=sys.stderr)
    sys.exit(1)


def _make_clean_doc() -> None:
    out = FIXTURES_DIR / "clean_doc.pdf"
    c = canvas.Canvas(str(out), pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(72, 800, "AICTE Approval Process Handbook — Test Document")
    c.drawString(72, 780, "Land area: 5.2 acres. Survey No: 123/4A.")
    c.drawString(72, 760, "Fire NOC valid until 2025-12-31.")
    c.showPage()
    c.setFont("Helvetica", 10)
    c.drawString(72, 800, "Page 2: Faculty list attached.")
    c.showPage()
    c.save()
    print(f"  Created: {out.name}")


def _make_tampered_js() -> None:
    """Inject a /JS token into raw PDF bytes."""
    import io
    out = FIXTURES_DIR / "tampered_js.pdf"
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(72, 800, "Tampered Document — contains JavaScript marker.")
    c.showPage()
    c.save()
    raw = buf.getvalue()
    # Inject /JS marker (does not execute; just for detector test)
    injected = raw.replace(b"%%EOF", b"/JS (app.alert('x');)\n%%EOF", 1)
    out.write_bytes(injected)
    print(f"  Created: {out.name}")


def _make_whiteout_page() -> None:
    """Draw white rectangle over text."""
    out = FIXTURES_DIR / "whiteout_page.pdf"
    c = canvas.Canvas(str(out), pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(72, 750, "Original text: Expiry Date 2022-03-15")
    # White rectangle over part of text
    c.setFillColorRGB(1, 1, 1)
    c.rect(200, 742, 200, 18, fill=1, stroke=0)
    # Replacement text on top
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Courier", 12)
    c.drawString(205, 750, "2025-12-31")
    c.showPage()
    c.save()
    print(f"  Created: {out.name}")


def _make_multi_font() -> None:
    """Use many font families on one page."""
    out = FIXTURES_DIR / "multi_font.pdf"
    c = canvas.Canvas(str(out), pagesize=A4)
    fonts = ["Helvetica", "Times-Roman", "Courier", "Helvetica-Bold", "Courier-Bold"]
    y = 780
    for i, font in enumerate(fonts):
        c.setFont(font, 10 + i)
        c.drawString(72, y, f"Font {font}: Sample regulatory text {i + 1}")
        y -= 30
    c.showPage()
    c.save()
    print(f"  Created: {out.name}")


def _make_scanned_stub() -> None:
    """Blank page — simulates a scanned image-only PDF."""
    out = FIXTURES_DIR / "scanned_stub.pdf"
    c = canvas.Canvas(str(out), pagesize=A4)
    # Blank page — no text layer
    c.showPage()
    c.save()
    print(f"  Created: {out.name}")


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating test fixtures in: {FIXTURES_DIR}\n")
    _make_clean_doc()
    _make_tampered_js()
    _make_whiteout_page()
    _make_multi_font()
    _make_scanned_stub()
    print("\n✅ All fixtures generated.")


if __name__ == "__main__":
    main()
