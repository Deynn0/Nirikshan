import React from "react";

export function Wordmark({ size = 28, className = "" }: { size?: number; className?: string }) {
  return (
    <div className={`inline-flex items-center gap-2.5 font-display font-bold tracking-tight text-ink ${className}`}>
      <span
        className="grid place-items-center rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 text-white shadow-xs"
        style={{ width: size, height: size }}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ width: size * 0.6, height: size * 0.6 }}
        >
          <path d="M2 12s3.8-7 10-7 10 7 10 7-3.8 7-10 7-10-7-10-7Z" />
          <circle cx="12" cy="12" r="3" fill="currentColor" stroke="none" />
        </svg>
      </span>
      <span className="text-[1.1875rem] font-bold tracking-[-0.02em] text-ink">
        Pramana <span className="text-[0.78rem] font-normal text-ink-3">/ Nirikshan</span>
      </span>
    </div>
  );
}
