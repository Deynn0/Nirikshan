import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      brand: {
        name: "Nirikshan",
        subname: "निरीक्षण",
        tagline: "AICTE Regulatory Scrutiny & Document Integrity System",
        airgapped: "STRICT AIR-GAP / LOCAL DEPLOYMENT",
      },
      nav: {
        portal: "Portal",
        applicant: "Applicant Portal",
        officer: "Officer Scrutiny Console",
        logout: "Sign Out",
        language: "Language",
        english: "English",
        hindi: "हिंदी",
      },
      auth: {
        loginTitle: "Sign in to Nirikshan",
        subtitle: "Offline Regulatory Verification Platform",
        username: "Officer / Institution ID",
        role: "Select Operational Role",
        applicantRole: "Applicant (Institution Registrar)",
        officerRole: "AICTE Scrutiny Officer",
        quickLogin: "Quick Demo Login",
        loginBtn: "Access Scrutiny Console",
        offlineNotice: "All cryptographic, OCR, and deterministic rule engines operate strictly on-premise without external telemetry.",
      },
      applicant: {
        title: "Institution Compliance Dossier",
        newDossier: "Register New Application Dossier",
        institutionName: "Institution Full Name",
        applicationNo: "Application Ref Number",
        program: "Program",
        level: "Level (UG/PG/Diploma)",
        locationType: "Location Type",
        intake: "Proposed Intake",
        uploadTitle: "Document Submissions & Verification",
        docType: "Document Type",
        selectDocType: "Select AICTE Document Category",
        dragDrop: "Drag and drop regulatory PDF or image here, or browse",
        fileSelected: "Selected file",
        uploadAndVerify: "Upload & Trigger Verification",
        liveProgress: "Live Processing Pipeline (SSE)",
        selfAssessmentTitle: "Pre-Submission Self-Assessment Check",
        selfAssessmentDesc: "Validate your regulatory claims against AICTE Approval Process Handbook (APH 2024-2027) norms before formal submission.",
        rectificationTitle: "Rectification & Deficiency Resolution",
        rectificationDesc: "Respond to deficiency observations issued by AICTE scrutiny officers with documentary justification.",
        submitRectification: "Submit Rectification Response",
        responseSent: "Rectification submitted successfully to the scrutiny officer.",
      },
      officer: {
        title: "Regulatory Scrutiny Console",
        dossierList: "Application Dossiers Under Scrutiny",
        documentsTab: "Documents & Evidence",
        viewerTab: "Document Viewer (pdf.js)",
        revisionTab: "Revision Time Machine",
        networkTab: "Integrity Network",
        geotagTab: "Geotag Verification Map",
        rulesTab: "Trust Ladder & Rule Findings",
        deficiencyTab: "Deficiency Letter Generator",
        askWhyTab: "Ask Why Assistant",
        trustLadder: "Evidence Trust Ladder",
        advisoryWarning: "Advisory: Machine Learning output is non-deterministic and requires human scrutiny.",
        exportPdf: "Export AICTE Deficiency Notice (PDF)",
      },
      trust: {
        level1: "Level 1: Cryptographic Proof (DSig / QR / Hash)",
        level2: "Level 2: Statutory Database (Direct Verification)",
        level3: "Level 3: Hardened Document (Microprint / Forensics)",
        level4: "Level 4: Advisory Model (YOLOX / LLM Extractor)",
        level5: "Level 5: Unverified Claim (Self-declaration)",
      },
      status: {
        pass: "COMPLIANT (PASS)",
        fail: "DEFICIENT (FAIL)",
        manual: "MANUAL SCRUTINY REQUIRED",
        tamper: "FLAGGED TAMPER / ANOMALY",
        inconclusive: "INCONCLUSIVE / PENDING",
      }
    }
  },
  hi: {
    translation: {
      brand: {
        name: "निरीक्षण",
        subname: "Nirikshan",
        tagline: "एआईसीटीई विनियामक संवीक्षा एवं दस्तावेज़ सत्यनिष्ठा प्रणाली",
        airgapped: "सख्त एयर-गैप / स्थानीय परिनियोजन",
      },
      nav: {
        portal: "पोर्टल",
        applicant: "आवेदक पोर्टल",
        officer: "अधिकारी संवीक्षा कंसोल",
        logout: "लॉग आउट",
        language: "भाषा",
        english: "English",
        hindi: "हिंदी",
      },
      auth: {
        loginTitle: "निरीक्षण में प्रवेश करें",
        subtitle: "ऑफ़लाइन विनियामक सत्यापन मंच",
        username: "अधिकारी / संस्थान पहचान",
        role: "परिचालन भूमिका चुनें",
        applicantRole: "आवेदक (संस्थान कुलसचिव)",
        officerRole: "एआईसीटीई संवीक्षा अधिकारी",
        quickLogin: "त्वरित डेमो लॉगिन",
        loginBtn: "संवीक्षा कंसोल खोलें",
        offlineNotice: "सभी क्रिप्टोग्राफ़िक, ओसीआर और नियम इंजन बिना किसी बाहरी नेटवर्क के सुरक्षित रूप से चलते हैं।",
      },
      applicant: {
        title: "संस्थान अनुपालन डॉसियर",
        newDossier: "नया आवेदन डॉसियर पंजीकृत करें",
        institutionName: "संस्थान का पूरा नाम",
        applicationNo: "आवेदन संदर्भ संख्या",
        program: "कार्यक्रम",
        level: "स्तर (यूजी/पीजी/डिप्लोमा)",
        locationType: "स्थान का प्रकार",
        intake: "प्रस्तावित प्रवेश क्षमता",
        uploadTitle: "दस्तावेज़ प्रस्तुति एवं सत्यापन",
        docType: "दस्तावेज़ प्रकार",
        selectDocType: "एआईसीटीई दस्तावेज़ श्रेणी चुनें",
        dragDrop: "पीडीएफ या छवि यहाँ खींचें या चुनें",
        fileSelected: "चयनित फ़ाइल",
        uploadAndVerify: "अपलोड करें एवं सत्यापन शुरू करें",
        liveProgress: "लाइव सत्यापन पाइपलाइन (एसएसई)",
        selfAssessmentTitle: "प्रस्तुति-पूर्व स्व-मूल्यांकन जांच",
        selfAssessmentDesc: "औपचारिक रूप से जमा करने से पहले एआईसीटीई अनुमोदन प्रक्रिया पुस्तिका (2024-2027) के अनुसार अपनी पात्रता की जांच करें।",
        rectificationTitle: "त्रुटि निवारण एवं अनुपालन उत्तर",
        rectificationDesc: "संवीक्षा अधिकारियों द्वारा पहचानी गई कमियों का दस्तावेजी साक्ष्य के साथ समाधान करें।",
        submitRectification: "सुधार उत्तर सबमिट करें",
        responseSent: "संवीक्षा अधिकारी को सुधार उत्तर सफलतापूर्वक प्रेषित किया गया।",
      },
      officer: {
        title: "विनियामक संवीक्षा कंसोल",
        dossierList: "संवीक्षाधीन आवेदन डॉसियर",
        documentsTab: "दस्तावेज़ एवं साक्ष्य",
        viewerTab: "दस्तावेज़ दर्शक (pdf.js)",
        revisionTab: "संशोधन टाइम मशीन",
        networkTab: "सत्यनिष्ठा नेटवर्क (ग्राफ़)",
        geotagTab: "जियोटैग सत्यापन मानचित्र",
        rulesTab: "ट्रस्ट लैडर एवं नियम निष्कर्ष",
        deficiencyTab: "कमी पत्र (Deficiency Letter) जनरेटर",
        askWhyTab: "\"क्यों पूछें\" सहायक",
        trustLadder: "साक्ष्य ट्रस्ट लैडर",
        advisoryWarning: "सलाहकारी: मशीन लर्निंग निष्कर्ष गैर-नियतात्मक हैं और मानवीय संवीक्षा अनिवार्य है।",
        exportPdf: "एआईसीटीई कमी सूचना (पीडीएफ) निर्यात करें",
      },
      trust: {
        level1: "स्तर 1: क्रिप्टोग्राफ़िक प्रमाण (डी-सिग / क्यूआर / हैश)",
        level2: "स्तर 2: सांविधिक डेटाबेस (प्रत्यक्ष सत्यापन)",
        level3: "स्तर 3: सुदृढ़ दस्तावेज़ (माइक्रोप्रिंट / फोरेंसिक)",
        level4: "स्तर 4: सलाहकारी मॉडल (YOLOX / एलएलएम एक्सट्रैक्टर)",
        level5: "स्तर 5: असत्यापित दावा (स्व-घोषणा)",
      },
      status: {
        pass: "अनुपालन पूर्ण (उत्तीर्ण)",
        fail: "नियम उल्लंघन (कमी पाई गई)",
        manual: "मानवीय संवीक्षा आवश्यक",
        tamper: "छेड़छाड़ / विसंगति चेतावनी",
        inconclusive: "अपूर्ण / लंबित",
      }
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
