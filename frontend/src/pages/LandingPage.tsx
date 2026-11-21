import React, { useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Eye,
  Users,
  Building2,
  MapPin,
  ExternalLink,
  ArrowUpDown,
} from 'lucide-react';
import { DocumentViewerWithMagnifier } from '../components/landing/DocumentViewerWithMagnifier';
import { VoxelFloorCanvas } from '../components/landing/VoxelFloorCanvas';
import { PramanaHeroHands } from '../components/landing/PramanaHeroHands';
import { LANDING_PALETTE } from '../landing/palette';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [wristY, setWristY] = useState<number | undefined>(undefined);
  const handleWristY = useCallback((y: number) => {
    setWristY(y);
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="lp min-h-screen bg-[#FAF8F4] text-stone-900 flex flex-col font-sans selection:bg-purple-200 selection:text-purple-900">
      {/* 
        HERO SECTION: Fits in exactly one viewport height (100vh),
        soft atmospheric gradient (peach -> soft apricot -> pink/rose -> light lilac),
        isometric purple voxel floor landscape,
        two expressive eye-inspired hand characters on the right half.
      */}
      <section
        className="relative h-screen max-h-[100vh] min-h-[660px] lg:min-h-[700px] w-full flex flex-col justify-between overflow-hidden"
        style={{
          background: LANDING_PALETTE.sky.gradient,
        }}
      >
        {/* Subtle atmospheric back-lighting behind right-side characters */}
        <div
          className="absolute top-[20%] right-[3%] lg:right-[8%] w-[500px] h-[500px] rounded-full pointer-events-none"
          style={{
            background: LANDING_PALETTE.sky.atmosphericBacklight,
            filter: 'blur(36px)',
            zIndex: 2,
          }}
        />

        {/* 1. Voxel floor — two canvas layers: back (z-0) and front (z-30) */}
        <VoxelFloorCanvas onWristY={handleWristY} />

        {/* 2. Hands — positioned gracefully on the right half (z-10) */}
        <PramanaHeroHands wristY={wristY} />

        {/* 3. Navbar: Floating clean white translucent pill with subtle warm shadow */}
        <header className="relative z-50 pt-4 px-4 sm:px-6 w-full flex justify-center">
          <nav className="w-full max-w-5xl px-6 py-2.5 rounded-full bg-white/92 backdrop-blur-md shadow-[0_4px_24px_rgba(0,0,0,0.05),0_1px_3px_rgba(0,0,0,0.02)] border border-white/95 flex items-center justify-between gap-4">
            {/* Logo: Nirikshan eye/iris symbol and title */}
            <Link to="/" className="flex items-center gap-2 group">
              <svg
                className="w-5 h-5 text-[#7B24E7] group-hover:scale-105 transition-transform"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M2 12s3.8-7 10-7 10 7 10 7-3.8 7-10 7-10-7-10-7Z" />
                <circle cx="12" cy="12" r="3.2" fill="#7B24E7" stroke="none" />
              </svg>
              <span className="font-extrabold text-[17px] tracking-tight text-stone-900">
                Nirikshan
              </span>
            </Link>

            {/* Center links */}
            <div className="hidden md:flex items-center gap-7 text-[13px] font-medium text-stone-700">
              <button
                onClick={() => scrollToSection('how-it-works')}
                className="hover:text-[#7B24E7] transition-colors cursor-pointer"
              >
                How it works
              </button>
              <button
                onClick={() => scrollToSection('edits')}
                className="hover:text-[#7B24E7] transition-colors cursor-pointer"
              >
                Edits
              </button>
              <button
                onClick={() => scrollToSection('cross-check')}
                className="hover:text-[#7B24E7] transition-colors cursor-pointer"
              >
                Cross-check
              </button>
              <button
                onClick={() => scrollToSection('trust-ladder')}
                className="hover:text-[#7B24E7] transition-colors cursor-pointer"
              >
                Trust ladder
              </button>
              <button
                onClick={() => scrollToSection('results')}
                className="hover:text-[#7B24E7] transition-colors cursor-pointer"
              >
                Results
              </button>
            </div>

            {/* Right: Purple pill button */}
            <button
              onClick={() => navigate('/workspace')}
              className="px-5 py-2 rounded-full bg-[#7B24E7] hover:bg-[#6A1BD6] active:bg-[#5815B6] text-white text-xs sm:text-[13px] font-semibold shadow-[0_2px_12px_rgba(123,36,231,0.35)] hover:shadow-[0_4px_16px_rgba(123,36,231,0.45)] active:scale-[0.98] transition-all shrink-0 flex items-center gap-1.5 cursor-pointer"
            >
              <span>Open workspace</span>
              <span className="text-sm font-normal">→</span>
            </button>
          </nav>
        </header>

        {/* 4. Hero Content: Two Columns, 10-11% from left edge on desktop */}
        <div className="relative z-20 flex-1 flex items-center w-full px-5 sm:px-8 lg:pl-[10.5%] lg:pr-10 py-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-center w-full max-w-[1440px]">
            {/* Left Column: max-w-[540px], bold Inter Tight headline, subtext, and CTA buttons */}
            <div className="lg:col-span-6 xl:col-span-6 flex flex-col items-start text-left z-20 relative max-w-[540px]">
              {/* Soft luminous white gradient glow behind the text container */}
              <div
                className="absolute -top-14 -left-12 w-[540px] h-[460px] rounded-full pointer-events-none"
                style={{
                  background: LANDING_PALETTE.sky.headlineGlow,
                  filter: 'blur(26px)',
                  zIndex: -1,
                }}
              />

              {/* Pill badge above headline */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-white/85 backdrop-blur-md border border-white/80 shadow-[0_2px_8px_rgba(0,0,0,0.04)] text-[#7C3AED] text-xs font-semibold mb-4 sm:mb-5">
                <span className="grid grid-cols-2 gap-0.5 w-2.5 h-2.5">
                  <span className="w-1 h-1 rounded-[1px] bg-[#7C3AED]" />
                  <span className="w-1 h-1 rounded-[1px] bg-[#7C3AED]" />
                  <span className="w-1 h-1 rounded-[1px] bg-[#7C3AED]" />
                  <span className="w-1 h-1 rounded-[1px] bg-[#7C3AED]" />
                </span>
                <span>PS 26261 · AICTE</span>
              </div>

              {/* Bold Inter Tight display headline — exactly 3 balanced lines */}
              <h1 className="font-display text-4xl sm:text-5xl lg:text-[56px] xl:text-[60px] 2xl:text-[62px] font-extrabold text-[#0F172A] tracking-[-0.035em] leading-[1.08] pb-1 overflow-visible">
                Every approval,<br />
                checked against<br />
                its evidence.
              </h1>

              {/* Complete description visible directly below heading, clear of voxel floor */}
              <p className="mt-4 sm:mt-5 text-xs sm:text-[13px] md:text-sm text-slate-600 leading-relaxed font-normal max-w-[480px]">
                Signatures, records and rules, verified at the source.<br className="hidden sm:inline" />
                Officials decide; Nirikshan shows the proof.
              </p>

              {/* Call to Action: Primary brand violet & Secondary translucent buttons */}
              <div className="mt-6 sm:mt-7 flex flex-wrap items-center gap-3.5">
                <button
                  onClick={() => navigate('/workspace')}
                  className="px-5 sm:px-6 py-2.5 sm:py-3 rounded-full bg-[#7B24E7] hover:bg-[#6A1BD6] active:bg-[#5815B6] text-white text-xs sm:text-[13px] font-semibold shadow-[0_4px_18px_rgba(123,36,231,0.35)] hover:shadow-[0_6px_24px_rgba(123,36,231,0.45)] active:scale-[0.98] transition-all flex items-center gap-1.5 group cursor-pointer"
                >
                  <span>Open the workspace</span>
                  <span className="text-sm group-hover:translate-x-0.5 transition-transform">→</span>
                </button>
                <button
                  onClick={() => scrollToSection('how-it-works')}
                  className="px-5 sm:px-6 py-2.5 sm:py-3 rounded-full bg-white/55 hover:bg-white/85 active:bg-white text-stone-900 border border-stone-300/80 shadow-xs hover:shadow-sm active:scale-[0.98] text-xs sm:text-[13px] font-semibold transition-all backdrop-blur-xs cursor-pointer"
                >
                  See how it works
                </button>
              </div>
            </div>

            {/* Right Column: spacious area occupied by the 3D hand characters */}
            <div className="lg:col-span-6 xl:col-span-6" aria-hidden="true" />
          </div>
        </div>

        {/* Bottom edge blending smoothly into off-white section below */}
        <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-t from-[#FAF8F4] to-transparent pointer-events-none z-30" />
      </section>

      {/* 4. Stat Cards Section (Below the Hero) */}
      <section id="results" className="py-14 sm:py-16 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="text-center mb-10">
          <span className="text-xs font-semibold uppercase tracking-wider text-stone-400">
            Measurable Regulatory Integrity
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900 mt-1">
            Field Evidence Reconciled At Scale
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Stat Card 1 */}
          <div className="surface-card bg-white border border-stone-200 rounded-xl p-6 shadow-soft hover:shadow-md transition-shadow flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-lg bg-purple-50 text-[#7B24E7] flex items-center justify-center mb-4">
                <Users className="w-5 h-5" />
              </div>
              <div className="text-3xl sm:text-4xl font-extrabold text-stone-900 tracking-tight">
                330 teachers
              </div>
              <p className="mt-2 text-xs text-stone-600 leading-relaxed">
                Cross-verified against EPF & state university rolls; eliminated duplicate ghost
                faculty.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-stone-100">
              <a
                href="https://aishe.gov.in"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-[#7B24E7] hover:text-[#6A1BD6] group"
              >
                Source: aishe.gov.in/faculty-roster
                <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </a>
            </div>
          </div>

          {/* Stat Card 2 */}
          <div className="surface-card bg-white border border-stone-200 rounded-xl p-6 shadow-soft hover:shadow-md transition-shadow flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center mb-4">
                <Building2 className="w-5 h-5" />
              </div>
              <div className="text-3xl sm:text-4xl font-extrabold text-stone-900 tracking-tight">
                7 colleges
              </div>
              <p className="mt-2 text-xs text-stone-600 leading-relaxed">
                Flagged across concurrent NOC applications in 3 districts sharing identical
                trustees and shell addresses.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-stone-100">
              <a
                href="https://aicte-india.org"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-[#7B24E7] hover:text-[#6A1BD6] group"
              >
                Source: aicte-india.org/eoa-directory
                <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </a>
            </div>
          </div>

          {/* Stat Card 3 */}
          <div className="surface-card bg-white border border-stone-200 rounded-xl p-6 shadow-soft hover:shadow-md transition-shadow flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
                <MapPin className="w-5 h-5" />
              </div>
              <div className="text-3xl sm:text-4xl font-extrabold text-stone-900 tracking-tight">
                9.61 acres
              </div>
              <p className="mt-2 text-xs text-stone-600 leading-relaxed">
                Digital land deed survey geometry reconciled with GIS revenue cadastre parcel
                boundaries.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-stone-100">
              <a
                href="https://maha-bhumi.gov.in"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-[#7B24E7] hover:text-[#6A1BD6] group"
              >
                Source: maha-bhumi.gov.in/cadastre-gis
                <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Interactive Document Viewer with Magnifier Lens & Revision List */}
      <section id="edits" className="py-12 md:py-16 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-[#7B24E7]">
              Document Forensics & Revision Tracking
            </span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-stone-900 mt-1">
              Forensic Magnifier & Tamper Detection
            </h3>
            <p className="text-xs sm:text-sm text-stone-600 max-w-xl mt-1">
              Inspect micro-alterations, overwritten glyphs, and post-signature appendages with
              real-time cryptographic verification.
            </p>
          </div>
        </div>

        <DocumentViewerWithMagnifier />
      </section>

      {/* 6. How It Works & Cross-Check Section */}
      <section id="how-it-works" className="py-16 bg-stone-100/60 border-y border-stone-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="text-xs font-semibold uppercase tracking-wider text-stone-400">
              Architecture & Workflow
            </span>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-stone-900 mt-1">
              Three Pillars of Autonomous Scrutiny
            </h3>
            <p className="text-xs sm:text-sm text-stone-600 mt-2">
              Moving from manual stamp-based checking to deterministic, cryptographic verification.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="surface-card bg-white border border-stone-200 rounded-xl p-6 shadow-soft">
              <div className="w-10 h-10 rounded-lg bg-purple-50 text-[#7B24E7] flex items-center justify-center font-bold text-sm mb-4">
                01
              </div>
              <h4 className="font-bold text-stone-900 text-base">
                Glyph & PDF Stream Forensics
              </h4>
              <p className="text-xs text-stone-600 mt-2 leading-relaxed">
                Scans byte offsets for incremental modifications post-signing, detecting font substitutions, layer overlays, and altered carpet areas.
              </p>
            </div>

            <div id="cross-check" className="surface-card bg-white border border-stone-200 rounded-xl p-6 shadow-soft">
              <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold text-sm mb-4">
                02
              </div>
              <h4 className="font-bold text-stone-900 text-base">
                Cross-Institutional Deduplication
              </h4>
              <p className="text-xs text-stone-600 mt-2 leading-relaxed">
                Hashes biometric and statutory employee records to uncover ghost faculty members shared across multiple sister institutions.
              </p>
            </div>

            <div id="trust-ladder" className="surface-card bg-white border border-stone-200 rounded-xl p-6 shadow-soft">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm mb-4">
                03
              </div>
              <h4 className="font-bold text-stone-900 text-base">
                Cryptographic Trust Ladder (E0–E5)
              </h4>
              <p className="text-xs text-stone-600 mt-2 leading-relaxed">
                Every fact is scored from E0 (unverified claim) to E5 (cryptographically attested PKCS#7 / sovereign Digilocker seal).
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Mandatory Footer Disclaimer */}
      <footer className="border-t border-stone-200 bg-[#FAF8F4] py-6 px-4">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-stone-500">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Nirikshan Statutory Verification Platform · WRO Pune</span>
          </div>
          <p className="text-center font-medium text-stone-600">
            Decision support only. Findings are preliminary indicators for review.
          </p>
          <div className="flex items-center gap-4 text-[11px]">
            <Link to="/workspace" className="text-[#7B24E7] hover:underline">
              Enter Workspace
            </Link>
            <span>v2.4.0-audit</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
