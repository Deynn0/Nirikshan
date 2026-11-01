"""Mobile-friendly QR verification scan endpoint for field inspection and public scrutiny.

GET /scan: Serves responsive mobile-friendly camera capture HTML page.
POST /scan: Ingests uploaded image (or payload JSON), verifies QR cryptographic signature,
and returns VALID, INVALID, or UNKNOWN_ISSUER.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from nirikshan.config import settings
from nirikshan.crypto.qr_verifier import (
    Keyring,
    QRVerificationStatus,
    decode_qr_from_image,
    verify_qr_payload,
)

router = APIRouter(tags=["Scan"])

SCAN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Nirikshan QR Verify | AICTE Document Integrity</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: rgba(23, 31, 48, 0.85);
      --card-border: rgba(255, 255, 255, 0.08);
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --valid: #10b981;
      --valid-bg: rgba(16, 185, 129, 0.15);
      --invalid: #f43f5e;
      --invalid-bg: rgba(244, 63, 94, 0.15);
      --unknown: #f59e0b;
      --unknown-bg: rgba(245, 158, 11, 0.15);
    }
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
    }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      background-image: radial-gradient(circle at 50% 0%, rgba(56, 189, 248, 0.12) 0%, transparent 60%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1rem;
    }
    .container {
      width: 100%;
      max-width: 440px;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    header {
      text-align: center;
      padding: 1rem 0 0.5rem;
    }
    .logo-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.35rem 0.75rem;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--accent);
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 0.75rem;
    }
    h1 {
      font-size: 1.5rem;
      font-weight: 800;
      letter-spacing: -0.025em;
      color: #fff;
    }
    p.subtitle {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }
    .card {
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 1.25rem;
      padding: 1.5rem;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }
    .upload-zone {
      border: 2px dashed rgba(56, 189, 248, 0.3);
      border-radius: 1rem;
      padding: 2rem 1rem;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s ease;
      background: rgba(15, 23, 42, 0.5);
    }
    .upload-zone:hover, .upload-zone:active {
      border-color: var(--accent);
      background: rgba(56, 189, 248, 0.05);
    }
    .icon-box {
      width: 56px;
      height: 56px;
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent);
      border-radius: 1rem;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 1rem;
    }
    .icon-box svg {
      width: 28px;
      height: 28px;
    }
    .upload-title {
      font-weight: 700;
      font-size: 1rem;
      margin-bottom: 0.25rem;
    }
    .upload-desc {
      font-size: 0.8rem;
      color: var(--text-muted);
    }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      width: 100%;
      padding: 0.85rem;
      border-radius: 0.75rem;
      font-size: 0.95rem;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      margin-top: 1rem;
    }
    .btn-primary {
      background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
      color: #fff;
      box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4);
    }
    .btn-primary:active {
      transform: scale(0.98);
    }
    input[type="file"] {
      display: none;
    }
    #previewContainer {
      display: none;
      margin-top: 1rem;
      border-radius: 0.75rem;
      overflow: hidden;
      border: 1px solid var(--card-border);
      max-height: 200px;
    }
    #previewImg {
      width: 100%;
      height: auto;
      display: block;
      object-fit: cover;
    }
    .result-card {
      display: none;
      margin-top: 1rem;
      padding: 1.25rem;
      border-radius: 1rem;
      animation: fadeIn 0.3s ease forwards;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .result-card.status-VALID {
      background: var(--valid-bg);
      border: 1px solid var(--valid);
      color: #ecfdf5;
    }
    .result-card.status-INVALID {
      background: var(--invalid-bg);
      border: 1px solid var(--invalid);
      color: #fff1f2;
    }
    .result-card.status-UNKNOWN_ISSUER {
      background: var(--unknown-bg);
      border: 1px solid var(--unknown);
      color: #fffbeb;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.35rem 0.75rem;
      border-radius: 0.5rem;
      font-weight: 800;
      font-size: 1.1rem;
      letter-spacing: 0.05em;
      margin-bottom: 0.75rem;
    }
    .status-VALID .badge {
      background: var(--valid);
      color: #064e3b;
    }
    .status-INVALID .badge {
      background: var(--invalid);
      color: #881337;
    }
    .status-UNKNOWN_ISSUER .badge {
      background: var(--unknown);
      color: #78350f;
    }
    .detail-row {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
      margin-top: 0.5rem;
      font-size: 0.85rem;
    }
    .detail-label {
      color: var(--text-muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      font-weight: 600;
    }
    .detail-val {
      font-weight: 600;
      color: #fff;
    }
    pre.code-data {
      margin-top: 0.75rem;
      padding: 0.75rem;
      background: rgba(0, 0, 0, 0.4);
      border-radius: 0.5rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      overflow-x: auto;
      max-height: 150px;
      color: #e2e8f0;
      white-space: pre-wrap;
      word-break: break-all;
    }
    .spinner {
      display: none;
      width: 24px;
      height: 24px;
      border: 3px solid rgba(255,255,255,0.2);
      border-radius: 50%;
      border-top-color: #fff;
      animation: spin 0.8s linear infinite;
      margin: 1rem auto 0;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    footer {
      margin-top: auto;
      padding: 1.5rem 0;
      font-size: 0.75rem;
      color: var(--text-muted);
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo-badge">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        AICTE NIRIKSHAN
      </div>
      <h1>Scrutiny QR Scanner</h1>
      <p class="subtitle">Cryptographic field verification of regulatory seals & NOCs</p>
    </header>

    <div class="card">
      <form id="scanForm" action="/scan" method="POST" enctype="multipart/form-data">
        <label for="cameraInput" class="upload-zone" id="dropArea">
          <div class="icon-box">
            <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
          </div>
          <div class="upload-title">Scan QR / Take Photo</div>
          <div class="upload-desc">Tap to open mobile camera or browse gallery</div>
        </label>
        <input type="file" id="cameraInput" name="file" accept="image/*" capture="environment">

        <div id="previewContainer">
          <img id="previewImg" alt="Scan preview">
        </div>

        <button type="button" class="btn btn-primary" id="scanBtn" style="display:none;">Verify Certificate QR</button>
        <div class="spinner" id="spinner"></div>
      </form>

      <div id="resultBox" class="result-card">
        <div class="badge" id="resStatus">STATUS</div>
        <p id="resDetails" style="font-size:0.85rem; margin-bottom:0.5rem;"></p>
        <div class="detail-row" id="rowIssuer">
          <span class="detail-label">Verified Authority</span>
          <span class="detail-val" id="resIssuer">-</span>
        </div>
        <div class="detail-row" id="rowKey">
          <span class="detail-label">Public Key Fingerprint</span>
          <span class="detail-val" id="resKeyId">-</span>
        </div>
        <div class="detail-row" id="rowTrust">
          <span class="detail-label">Trust Ladder Standing</span>
          <span class="detail-val" id="resTrust">-</span>
        </div>
        <div class="detail-row" id="rowData">
          <span class="detail-label">Endorsed Document Data</span>
          <pre class="code-data" id="resData"></pre>
        </div>
      </div>
    </div>

    <footer>
      Protected by Nirikshan Offline Cryptographic Trust Ladder<br>
      Air-Gapped Indian PKI & Ed25519/ECDSA Engine
    </footer>
  </div>

  <script>
    const fileInput = document.getElementById('cameraInput');
    const previewContainer = document.getElementById('previewContainer');
    const previewImg = document.getElementById('previewImg');
    const scanBtn = document.getElementById('scanBtn');
    const spinner = document.getElementById('spinner');
    const resultBox = document.getElementById('resultBox');

    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (evt) => {
        previewImg.src = evt.target.result;
        previewContainer.style.display = 'block';
        scanBtn.style.display = 'flex';
        resultBox.style.display = 'none';
        // Auto-trigger verification on camera capture
        submitScan(file);
      };
      reader.readAsDataURL(file);
    });

    scanBtn.addEventListener('click', () => {
      if (fileInput.files[0]) {
        submitScan(fileInput.files[0]);
      }
    });

    async function submitScan(file) {
      spinner.style.display = 'block';
      scanBtn.style.display = 'none';
      resultBox.style.display = 'none';

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('/scan', {
          method: 'POST',
          body: formData,
          headers: { 'Accept': 'application/json' }
        });
        const data = await res.json();
        showResult(data);
      } catch (err) {
        showResult({
          status: 'INVALID',
          details: 'Network error or unable to contact scrutiny service.'
        });
      } finally {
        spinner.style.display = 'none';
        scanBtn.style.display = 'flex';
      }
    }

    function showResult(data) {
      resultBox.className = 'result-card status-' + data.status;
      document.getElementById('resStatus').innerText = data.status;
      document.getElementById('resDetails').innerText = data.details || (data.status === 'VALID' ? 'Endorsed by authorized issuer officer.' : 'Verification issue detected.');
      document.getElementById('resIssuer').innerText = data.issuer || 'Unidentified Authority';
      document.getElementById('resKeyId').innerText = data.key_id || 'N/A';
      document.getElementById('resTrust').innerText = data.trust_ladder_level || (data.status === 'VALID' ? 'CRYPTOGRAPHIC (Rank 60)' : 'STRUCTURAL_FORENSIC');

      const dataBox = document.getElementById('resData');
      if (data.data) {
        dataBox.innerText = typeof data.data === 'object' ? JSON.stringify(data.data, null, 2) : String(data.data);
        document.getElementById('rowData').style.display = 'flex';
      } else {
        document.getElementById('rowData').style.display = 'none';
      }

      resultBox.style.display = 'block';
    }
  </script>
</body>
</html>
"""


@router.get("/scan", response_class=HTMLResponse)
async def scan_page() -> HTMLResponse:
    """Serve the public mobile-friendly QR scanner page."""
    return HTMLResponse(content=SCAN_HTML, status_code=200)


@router.post("/scan")
async def scan_verify(
    request: Request,
    file: UploadFile | None = File(default=None),
) -> Any:
    """Verify QR code from uploaded image or direct JSON payload."""
    content_type = request.headers.get("content-type", "")
    accept_header = request.headers.get("accept", "")

    raw_payload_data = None
    image_bytes = None

    # 1. Check if multipart file upload
    if file:
        image_bytes = await file.read()
        if len(image_bytes) > settings.sandbox_max_file_size_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "status": QRVerificationStatus.INVALID.value,
                    "details": f"File size exceeds sandbox security limit ({settings.sandbox_max_file_size_bytes} bytes).",
                },
            )
    elif "application/json" in content_type:
        try:
            body = await request.json()
            if "image_base64" in body:
                import base64
                image_bytes = base64.b64decode(body["image_base64"])
            elif "payload" in body:
                raw_payload_data = body["payload"]
            elif "data" in body and "signature" in body and "key_id" in body:
                raw_payload_data = body
        except Exception:
            return JSONResponse(
                status_code=400,
                content={"status": QRVerificationStatus.INVALID.value, "details": "Malformed JSON request."},
            )

    keyring = Keyring()

    # 2. If image bytes provided, decode QR
    if image_bytes:
        decoded_codes = decode_qr_from_image(image_bytes)
        if not decoded_codes:
            response_data = {
                "status": QRVerificationStatus.INVALID.value,
                "details": "No readable QR code found in uploaded image.",
                "is_tampered": True,
                "trust_ladder_level": "STRUCTURAL_FORENSIC",
                "trust_rank": 20,
            }
            if "text/html" in accept_header and "application/json" not in accept_header:
                return HTMLResponse(content=SCAN_HTML, status_code=200)
            return JSONResponse(status_code=200, content=response_data)

        # Use first decoded QR code
        raw_payload_data = decoded_codes[0]

    if not raw_payload_data:
        return JSONResponse(
            status_code=400,
            content={"status": QRVerificationStatus.INVALID.value, "details": "No payload or image provided."},
        )

    # 3. Cryptographically verify QR payload
    result = verify_qr_payload(raw_payload_data, keyring=keyring)

    ev_dict = result.evidence_item.model_dump() if result.evidence_item else None
    trust_level_str = result.evidence_item.trust_level.value if result.evidence_item else "STRUCTURAL_FORENSIC"
    trust_rank = result.evidence_item.trust_rank if result.evidence_item else 20

    resp_content = {
        "status": result.status.value,
        "key_id": result.key_id,
        "issuer": result.issuer,
        "role": result.role,
        "data": result.data,
        "is_tampered": result.is_tampered,
        "details": result.details,
        "trust_ladder_level": trust_level_str,
        "trust_rank": trust_rank,
        "evidence_item": ev_dict,
    }

    return JSONResponse(content=resp_content, status_code=200)
