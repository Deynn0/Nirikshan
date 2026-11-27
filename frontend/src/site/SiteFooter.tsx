import React from "react";
import { Link } from "react-router-dom";
import { ShieldCheck } from "lucide-react";

export function SiteFooter({ className = "" }: { className?: string }) {
  return (
    <footer className={`mt-auto pt-6 text-[0.75rem] text-ink-3 ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-line pt-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="size-4 text-brand-600" aria-hidden />
          <span>Nirikshan Regulatory Verification Platform</span>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-ink-3">
          <Link to="/" className="hover:text-ink transition-colors">
            Overview
          </Link>
          <a
            href="https://www.aicte-india.org"
            target="_blank"
            rel="noreferrer"
            className="hover:text-ink transition-colors"
          >
            AICTE India
          </a>
          <span>&copy; {new Date().getFullYear()} Regulatory Scrutiny Cell</span>
        </div>
      </div>
    </footer>
  );
}
