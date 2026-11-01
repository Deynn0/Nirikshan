import '@testing-library/jest-dom/vitest';
import '@testing-library/jest-dom';
import '../i18n';

// Mock window.matchMedia if needed by jsdom
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});
