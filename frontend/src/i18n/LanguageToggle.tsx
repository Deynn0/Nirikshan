import React from 'react';
import { useTranslation } from 'react-i18next';
import { Languages } from 'lucide-react';

export function LanguageToggle() {
  const { i18n } = useTranslation();
  const current = i18n.language.startsWith('hi') ? 'hi' : 'en';

  const toggle = () => {
    i18n.changeLanguage(current === 'en' ? 'hi' : 'en');
  };

  return (
    <button
      type="button"
      onClick={toggle}
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[0.8125rem] font-medium text-ink-3 transition-colors hover:bg-surface-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-brand-500 cursor-pointer"
      aria-label="Toggle language"
    >
      <Languages className="size-3.5" aria-hidden />
      <span>{current === 'en' ? 'English' : 'हिंदी'}</span>
    </button>
  );
}
