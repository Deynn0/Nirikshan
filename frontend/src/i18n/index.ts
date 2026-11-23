import i18n from 'i18next';
import { initReactI18next, useTranslation } from 'react-i18next';

export { LanguageToggle } from './LanguageToggle';

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
      "Sign in": "Sign in",
      "Sign in to review": "Sign in to review",
      "Pramana workspace": "Pramana workspace",
      "Officials": "Officials",
      "Institutions": "Institutions",
      "Simulated": "Simulated",
      "One click signs in with the shared demo password.": "One click signs in with the shared demo password.",
      "Pre-configured synthetic profiles for regulatory testing.": "Pre-configured synthetic profiles for regulatory testing.",
      "Demo accounts (synthetic data)": "Demo accounts (synthetic data)",
      "Demo accounts are not available right now.": "Demo accounts are not available right now.",
      "Username": "Username",
      "Password": "Password",
      "Skip to content": "Skip to content",
      "Back to overview": "Back to overview",
      "Holding a certificate with a QR code?": "Holding a certificate with a QR code?",
      "Scan it to check the issuer's signature. No sign-in needed.": "Scan it to check the issuer's signature. No sign-in needed.",
      "Sign in failed": "Sign in failed",
      "Show fewer institutions": "Show fewer institutions",
      "Show all {n} institutions": "Show all {n} institutions",
      "Scrutiny officer": "Scrutiny officer",
      "Verification cell": "Verification cell",
      "Administrator and auditor": "Administrator and auditor",
      "Institution applicant": "Institution applicant",
      "Accessibility options": "Accessibility options",
      "Text size": "Text size",
      "Contrast": "Contrast",
      "Theme": "Theme",
      "Accessibility statement": "Accessibility statement",
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
      "Sign in": "साइन इन करें",
      "Sign in to review": "समीक्षा के लिए साइन इन करें",
      "Pramana workspace": "प्रमाण कार्यक्षेत्र",
      "Officials": "अधिकारी",
      "Institutions": "संस्थान",
      "Simulated": "सिम्युलेटेड",
      "One click signs in with the shared demo password.": "एक क्लिक में साझा डेमो पासवर्ड से साइन इन करें।",
      "Demo accounts (synthetic data)": "डेमो खाते (सिंथेटिक डेटा)",
      "Username": "उपयोगकर्ता नाम",
      "Password": "पासवर्ड",
      "Back to overview": "अवलोकन पर वापस जाएँ",
      "Holding a certificate with a QR code?": "क्या आपके पास क्यूआर कोड वाला प्रमाणपत्र है?",
      "Scan it to check the issuer's signature. No sign-in needed.": "जारीकर्ता के हस्ताक्षर की जांच के लिए इसे स्कैन करें। साइन-इन की आवश्यकता नहीं है।",
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

export function useT() {
  const { t } = useTranslation();
  return (key: string) => t(key, { defaultValue: key });
}

export function useLang() {
  const { t, i18n: i18nInst } = useTranslation();
  const tn = (count: number, singular: string, plural: string) => {
    const text = count === 1 ? singular : plural;
    return text.replace('{n}', String(count));
  };
  return {
    t: (key: string) => t(key, { defaultValue: key }),
    tn,
    lang: i18nInst.language,
    setLang: (lang: string) => i18nInst.changeLanguage(lang),
  };
}

export default i18n;
