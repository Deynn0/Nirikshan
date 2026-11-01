export interface ApplicationItem {
  id: string;
  name: string;
  category: 'Engineering' | 'Management' | 'Pharmacy' | 'Polytechnic';
  status: 'Under review' | 'Needs attention' | 'SIMULATED' | 'E5 Verified' | 'High Risk';
  statusType: 'critical' | 'warning' | 'verified' | 'neutral';
  openFindings: number;
  riskScore: number;
  location: string;
  submittedAt: string;
  strongestProof: string;
}

export interface ProofStrengthRow {
  requirement: string;
  declared: 'green' | 'amber' | 'red' | 'gray';
  present: 'green' | 'amber' | 'red' | 'gray';
  read: 'green' | 'amber' | 'red' | 'gray';
  aicteRecord: 'green' | 'amber' | 'red' | 'gray';
  issuerRegistry: 'green' | 'amber' | 'red' | 'gray';
  signatureQr: 'green' | 'amber' | 'red' | 'gray';
  strongestProof: string;
  statusBadge: string;
}

export interface FindingDetail {
  id: string;
  group: 'Validity' | 'Verification' | 'Document forensics';
  title: string;
  severity: 'critical' | 'warning' | 'verified';
  severityLabel: string;
  ruleId: string;
  description: string;
  recommendation: string;
  documentRef: string;
  pageNumber: number;
  evidenceSnippet: string;
  evidenceHash: string;
  statutoryReference: string;
}

export interface LinkedNode {
  id: string;
  label: string;
  type: 'college' | 'trust' | 'person' | 'document';
  status?: string;
  x: number;
  y: number;
}

export interface LinkedEdge {
  source: string;
  target: string;
  label: string;
  suspicious?: boolean;
}

export const mockApplications: ApplicationItem[] = [
  {
    id: 'APP-2026-AICTE-4891',
    name: 'Apex Institute of Technology & Management',
    category: 'Engineering',
    status: 'Under review',
    statusType: 'critical',
    openFindings: 5,
    riskScore: 78,
    location: 'Pune, Maharashtra (WRO)',
    submittedAt: '2026-03-24',
    strongestProof: 'E4 Digilocker',
  },
  {
    id: 'APP-2026-AICTE-4892',
    name: 'Trinity Polytechnic Institute',
    category: 'Polytechnic',
    status: 'Needs attention',
    statusType: 'critical',
    openFindings: 6,
    riskScore: 86,
    location: 'Nashik, Maharashtra (WRO)',
    submittedAt: '2026-03-22',
    strongestProof: 'E3 Statutory OCR',
  },
  {
    id: 'APP-2026-AICTE-4893',
    name: 'Pioneer College of Pharmacy',
    category: 'Pharmacy',
    status: 'E5 Verified',
    statusType: 'verified',
    openFindings: 0,
    riskScore: 12,
    location: 'Nagpur, Maharashtra (WRO)',
    submittedAt: '2026-03-21',
    strongestProof: 'E5 Cryptographic PSS',
  },
  {
    id: 'APP-2026-AICTE-4894',
    name: 'Saraswati School of Management',
    category: 'Management',
    status: 'Under review',
    statusType: 'warning',
    openFindings: 2,
    riskScore: 42,
    location: 'Aurangabad, Maharashtra (WRO)',
    submittedAt: '2026-03-20',
    strongestProof: 'E4 Digilocker',
  },
  {
    id: 'APP-2026-AICTE-4895',
    name: 'Deccan College of Engineering & Research',
    category: 'Engineering',
    status: 'Needs attention',
    statusType: 'critical',
    openFindings: 4,
    riskScore: 74,
    location: 'Kolhapur, Maharashtra (WRO)',
    submittedAt: '2026-03-19',
    strongestProof: 'E3 Statutory OCR',
  },
  {
    id: 'APP-2026-AICTE-4896',
    name: 'Sterling Global Institute',
    category: 'Management',
    status: 'SIMULATED',
    statusType: 'neutral',
    openFindings: 1,
    riskScore: 20,
    location: 'Navi Mumbai, Maharashtra (WRO)',
    submittedAt: '2026-03-18',
    strongestProof: 'E5 Cryptographic PSS',
  },
  {
    id: 'APP-2026-AICTE-4897',
    name: 'Vardhaman Institute of Technology',
    category: 'Polytechnic',
    status: 'High Risk',
    statusType: 'critical',
    openFindings: 7,
    riskScore: 91,
    location: 'Solapur, Maharashtra (WRO)',
    submittedAt: '2026-03-15',
    strongestProof: 'E1 Declared only',
  },
];

export const mockProofStrengthRows: ProofStrengthRow[] = [
  {
    requirement: 'Faculty:Student Ratio (1:15 Norm)',
    declared: 'green',
    present: 'green',
    read: 'green',
    aicteRecord: 'amber',
    issuerRegistry: 'red',
    signatureQr: 'red',
    strongestProof: 'E3 Statutory OCR (3 ghost faculty found in State DB)',
    statusBadge: 'Contradicted',
  },
  {
    requirement: 'Land Title & 30-Year Registered Lease',
    declared: 'green',
    present: 'green',
    read: 'green',
    aicteRecord: 'green',
    issuerRegistry: 'red',
    signatureQr: 'green',
    strongestProof: 'E4 Digilocker (18 yrs remaining lease vs 30 yrs)',
    statusBadge: 'Warning',
  },
  {
    requirement: 'Built-up Carpet Area (12,450 sqm)',
    declared: 'green',
    present: 'green',
    read: 'green',
    aicteRecord: 'green',
    issuerRegistry: 'green',
    signatureQr: 'green',
    strongestProof: 'E5 Cryptographic PSS (Architect Digital Seal)',
    statusBadge: 'Verified',
  },
  {
    requirement: 'Prior AICTE Extension of Approval (EoA)',
    declared: 'green',
    present: 'green',
    read: 'green',
    aicteRecord: 'green',
    issuerRegistry: 'green',
    signatureQr: 'green',
    strongestProof: 'E5 Central Portal Hash Match (2025-26)',
    statusBadge: 'Verified',
  },
  {
    requirement: 'Fire Safety & Occupancy Certificate',
    declared: 'green',
    present: 'green',
    read: 'green',
    aicteRecord: 'amber',
    issuerRegistry: 'amber',
    signatureQr: 'green',
    strongestProof: 'E4 Municipal CFO Portal (Valid till Aug 2026)',
    statusBadge: 'Verified',
  },
  {
    requirement: 'Corpus Fund Statutory Fixed Deposit',
    declared: 'green',
    present: 'green',
    read: 'green',
    aicteRecord: 'green',
    issuerRegistry: 'green',
    signatureQr: 'red',
    strongestProof: 'E3 Bank Branch FDR (Lien renewal pending)',
    statusBadge: 'Warning',
  },
  {
    requirement: 'Laboratory Equipment & Workstations',
    declared: 'green',
    present: 'green',
    read: 'green',
    aicteRecord: 'green',
    issuerRegistry: 'gray',
    signatureQr: 'green',
    strongestProof: 'E5 EXIF Photogrammetry + Geotag Proven',
    statusBadge: 'Verified',
  },
];

export const mockFindings: FindingDetail[] = [
  {
    id: 'F-001',
    group: 'Validity',
    title: 'Land lease term is 18 years vs 30 years statutory requirement',
    severity: 'critical',
    severityLabel: 'Critical',
    ruleId: 'RULE-LND-02',
    description:
      'AICTE Approval Process Handbook (Clause 4.1.2) stipulates that land for self-financing institutions must be held under a registered lease of at least 30 continuous years. Sub-registrar Deed #4192/2014 covenants run until 2044 (remaining: 18 years, 4 months), which violates the 30-year active horizon required on the date of scrutiny.',
    recommendation:
      'Issue deficiency memo requesting supplementary registered lease extension deed for minimum 30 years before final scrutiny committee.',
    documentRef: 'Registered_Lease_Deed_SubRegistrar_Pune.pdf',
    pageNumber: 4,
    evidenceSnippet:
      '"...hereby demised unto the Lessee for a term of twenty-five (25) years commencing from 1st April 2014 and ending on 31st March 2039 with conditional five-year option..."',
    evidenceHash: 'sha256:4d83e2f1839a829104ebc7612c77d9401bf5199859f14ba6',
    statutoryReference: 'AICTE APH 2026-27, Appx 4, Cl 4.1.2 (Land Norms)',
  },
  {
    id: 'F-002',
    group: 'Validity',
    title: 'Corpus FD lien endorsement expires prior to academic session closure',
    severity: 'warning',
    severityLabel: 'Warning',
    ruleId: 'RULE-FIN-09',
    description:
      'Statutory joint FDR of ₹1,00,00,000/- with Regional Officer AICTE has maturity date 2026-07-31. Regulatory guidelines mandate lien validity must extend at least 6 months beyond the current academic year (minimum 2027-02-28).',
    recommendation: 'Require applicant to submit Bank Auto-Renewal Lien letter from State Bank of India.',
    documentRef: 'Fixed_Deposit_Receipt_SBI_Lien.pdf',
    pageNumber: 1,
    evidenceSnippet:
      '"Maturity Date: 31-07-2026 | Lien marked in favor of Regional Officer AICTE WRO until maturity date only."',
    evidenceHash: 'sha256:99bc181e491823a0df47291884ccbb1947209938dcb92841',
    statutoryReference: 'AICTE APH 2026-27, Appx 5, Cl 5.3 (Financial Security Deposit)',
  },
  {
    id: 'F-003',
    group: 'Verification',
    title: '3 Faculty Aadhaar hashes match concurrent filings at Apex College Solapur',
    severity: 'critical',
    severityLabel: 'Critical',
    ruleId: 'RULE-FAC-15',
    description:
      'Cross-registry deduplication flagged Dr. V. R. Patil (Professor, Comp Sci), Prof. S. N. Kulkarni (Assoc Prof, Mech), and Dr. M. G. Joshi (Professor, Electrical). Their hashed biometric keys and EPF numbers appear simultaneously in Application APP-2026-AICTE-4897 (Apex College Solapur).',
    recommendation:
      'Trigger multi-college institutional audit and disqualify duplicate faculty headcount from the student-teacher ratio computation.',
    documentRef: 'Faculty_Roster_With_Aadhaar_Hashes.pdf',
    pageNumber: 8,
    evidenceSnippet:
      '"Patil Vilas R. | EPF: MH/BAN/0048192/001 | Hashed ID: b2940af1...c49a | Assigned: Full-Time Regular Professor"',
    evidenceHash: 'sha256:2b940af1940182810398ef91882c199846bfa993018274ac',
    statutoryReference: 'AICTE Anti-Ghost Faculty Guideline, Gaz. Notif. 2025/144',
  },
  {
    id: 'F-004',
    group: 'Verification',
    title: 'Principal PhD degree serial number not found in University convocation roll',
    severity: 'warning',
    severityLabel: 'Warning',
    ruleId: 'RULE-FAC-01',
    description:
      'Dr. Anand R. Kothari declared PhD from SPPU Pune (2014, Reg #ENG/7182). Automated API check against SPPU Convocation Registry returned status "RECORD_NOT_LOCATED_IN_YEAR_BATCH".',
    recommendation: 'Request official sealed verification transcript from University Registrar.',
    documentRef: 'Principal_Appointment_and_Credentials.pdf',
    pageNumber: 3,
    evidenceSnippet:
      '"Degree of Doctor of Philosophy in Mechanical Engineering awarded on 18th Feb 2014, Roll ENG-7182."',
    evidenceHash: 'sha256:7198ccba0194819772384910293847192837401928347102',
    statutoryReference: 'AICTE Norms for Principal / Director Eligibility (Table 2.1)',
  },
  {
    id: 'F-005',
    group: 'Document forensics',
    title: 'Modified PDF font stream detected post-digital signature',
    severity: 'critical',
    severityLabel: 'Critical',
    ruleId: 'RULE-SEC-04',
    description:
      'Document forensics detected incremental PDF stream append at byte offset 0x004F8A20 occurring after the cryptographic PKCS#7 signature timestamp. An embedded font replacement alters the numeric text on Page 12 from "Built-up area: 8,450 sqm" to "Built-up area: 12,450 sqm".',
    recommendation:
      'Reject the altered PDF; demand raw CAD vector drawing certified with fresh digital signature from licensed chartered engineer.',
    documentRef: 'Architect_Builtup_Area_Certificate.pdf',
    pageNumber: 12,
    evidenceSnippet:
      '"[PDF Forensic Alert] Byte stream altered post-signature. Font ArialMT glyph /four swapped to /eight."',
    evidenceHash: 'sha256:ff0189a81729401729837492817492837491827394817293',
    statutoryReference: 'IT Act 2000 Sec 65B & AICTE Digital Evidence Policy 2026',
  },
];

export const mockLinkedNodes: LinkedNode[] = [
  { id: 'app1', label: 'Apex Inst. Pune', type: 'college', status: 'critical', x: 200, y: 150 },
  { id: 'trust', label: 'Vidya Vikas Trust', type: 'trust', status: 'neutral', x: 200, y: 50 },
  { id: 'app2', label: 'Trinity Poly', type: 'college', status: 'critical', x: 70, y: 220 },
  { id: 'app3', label: 'Pioneer Pharmacy', type: 'college', status: 'verified', x: 330, y: 220 },
  { id: 'p1', label: 'K. R. Deshmukh (Trustee)', type: 'person', status: 'warning', x: 100, y: 80 },
  { id: 'f1', label: 'Dr. V. Patil (Ghost Fac)', type: 'person', status: 'critical', x: 200, y: 270 },
  { id: 'app4', label: 'Apex Solapur', type: 'college', status: 'critical', x: 200, y: 350 },
];

export const mockLinkedEdges: LinkedEdge[] = [
  { source: 'trust', target: 'app1', label: 'Parent Trust' },
  { source: 'trust', target: 'app2', label: 'Parent Trust' },
  { source: 'p1', target: 'trust', label: 'Chairman' },
  { source: 'p1', target: 'app3', label: 'Trustee Signer' },
  { source: 'app1', target: 'f1', label: 'Employed As Full-Time', suspicious: true },
  { source: 'app4', target: 'f1', label: 'Concurrent Roll', suspicious: true },
  { source: 'app1', target: 'app2', label: 'Common Registered Address' },
];

export const mockCertCoverage = [
  { name: 'Fire Safety NOC', start: '2023-08-30', end: '2026-08-30', status: 'verified', note: '172 days remaining' },
  { name: 'Building Structural Stability', start: '2022-05-15', end: '2027-05-15', status: 'verified', note: 'Valid' },
  { name: 'Registered Land Lease (30y)', start: '2014-04-01', end: '2039-03-31', status: 'warning', note: 'Only 18y remaining (30y required)' },
  { name: 'University Affiliation (SPPU)', start: '2025-07-01', end: '2026-06-30', status: 'verified', note: 'Annual renewal' },
  { name: 'Pollution Control Consent', start: '2020-01-01', end: '2025-12-31', status: 'critical', note: 'EXPIRED (Renewal Gap 63 days)' },
];

export const mockAuditTrail = [
  {
    id: 'TX-901',
    timestamp: '2026-03-24 16:42:10 IST',
    actor: 'System OCR Pipeline',
    action: 'Document ingestion & high-resolution glyph extraction',
    hash: 'sha256:7f9a2b0e...e148c7d',
    status: 'Verified',
  },
  {
    id: 'TX-902',
    timestamp: '2026-03-24 16:42:18 IST',
    actor: 'Forensic PDF Stream Analyzer',
    action: 'Flagged font glyph substitution in Architect Certificate Page 12',
    hash: 'sha256:4d83e2f1...77d9401',
    status: 'Contradicted',
  },
  {
    id: 'TX-903',
    timestamp: '2026-03-24 16:42:35 IST',
    actor: 'Cross-Registry Deduplicator',
    action: 'Cross-checked 64 faculty hashes against State EPF / AISHE DB',
    hash: 'sha256:2b940af1...018274a',
    status: 'High Alert',
  },
  {
    id: 'TX-904',
    timestamp: '2026-03-24 17:15:02 IST',
    actor: 'Dr. Sunita Sharma (Senior Scrutiny Officer)',
    action: 'Annotated Land Lease Deed Clause 4.1 discrepancy',
    hash: 'sha256:bb0198aa...9182374',
    status: 'Signed',
  },
  {
    id: 'TX-905',
    timestamp: '2026-03-24 17:30:00 IST',
    actor: 'Nirikshan Merkle Anchor Node',
    action: 'Merkle root commitment published to statutory ledger',
    hash: 'sha256:a1b2c3d4...9e8f7a6',
    status: 'Chain Intact',
  },
];

export const mockAskWhyDialogues = [
  {
    id: 'q1',
    question: 'Why was the faculty ratio flagged as high risk?',
    answerSentences: [
      {
        text: 'The applicant declared 64 faculty members to satisfy the 1:15 statutory ratio for 960 total students.',
        citationId: 'C-01',
        citationTitle: 'Faculty Roster Page 2',
      },
      {
        text: 'However, cross-registry deduplication proved that 3 senior professors are concurrently listed as full-time faculty at Apex College Solapur.',
        citationId: 'C-02',
        citationTitle: 'AISHE Cross-Registry Deduplication Hash match',
        isWarning: true,
      },
      {
        text: 'Removing the 3 duplicate faculty drops the actual teacher count to 61, increasing the effective ratio to 1:15.74, which breaches mandatory AICTE norms.',
        citationId: 'C-03',
        citationTitle: 'AICTE APH 2026 Table 2.1 Cadre Ratio',
        isCritical: true,
      },
    ],
  },
  {
    id: 'q2',
    question: 'What is the exact discrepancy in the land deed title?',
    answerSentences: [
      {
        text: 'Sub-registrar Deed #4192/2014 was executed on 1st April 2014 for an initial tenure of 25 years with a 5-year option.',
        citationId: 'C-04',
        citationTitle: 'Registered Lease Deed Page 4',
      },
      {
        text: 'AICTE regulations strictly require an unbroken minimum 30-year active lease from the scrutiny date.',
        citationId: 'C-05',
        citationTitle: 'Statutory Land Lease Guideline Clause 4.1.2',
      },
      {
        text: 'With only 18 years remaining on the active instrument, the campus title does not fulfill perpetual tenure prerequisites.',
        citationId: 'C-06',
        citationTitle: 'Title Validity Calculation Engine',
        isCritical: true,
      },
    ],
  },
  {
    id: 'q3',
    question: 'Can this application proceed under provisional or conditional approval?',
    answerSentences: [
      {
        text: 'Provisional approval cannot be granted while a critical document forensic modification (RULE-SEC-04) remains unresolved.',
        citationId: 'C-07',
        citationTitle: 'Architect Builtup Area Certificate Byte 0x004F8A20',
        isCritical: true,
      },
      {
        text: 'The Regional Scrutiny Officer must first issue a formal deficiency letter requiring an untampered digital original and an executed 30-year lease extension.',
        citationId: 'C-08',
        citationTitle: 'Scrutiny Committee Standing Order 4.3',
      },
    ],
  },
];
