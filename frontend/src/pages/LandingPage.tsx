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
    <div className="min-h-screen bg-[#FAF8F4] text-stone-900 flex flex-col font-sans selection:bg-purple-200 selection:text-purple-900">
      {/* 
        HERO SECTION: Fits in exactly one viewport height (100vh),
        warm color gradient from pink/orange to light yellow on top,
        pattern of low purple 3D grid blocks and larger purple and grey rectangular objects,
        two 3D hand sculptures with character eyes (pink looking sideways, purple looking up).
      */}
      <section
        className="relative h-screen max-h-[100vh] min-h-[640px] w-full flex flex-col justify-between overflow-hidden"
        style={{
          background:
            'linear-gradient(180deg, #FDC4A6 0%, #FDCDB1 16%, #FDDDC4 28%, #FEEBD8 38%, #FFF5EC 42.5%, #EAE2FC 43.5%, #CEBCFC 70%, #BAA4FB 100%)',
        }}
      >
        {/* 1. Voxel floor — two canvas layers: back (z-0) and front (z-30) */}
        <VoxelFloorCanvas onWristY={handleWristY} />

        {/* 2. Hands — absolute layer filling the hero so wristY maps 1:1 (z-10) */}
        <PramanaHeroHands wristY={wristY} />

        {/* 3. Navbar: Floating white rounded pill with soft shadow */}
        <header className="relative z-50 pt-4 px-4 sm:px-6 w-full flex justify-center">
          <nav className="w-full max-w-5xl px-6 py-2.5 rounded-full bg-white/95 backdrop-blur-md shadow-[0_4px_24px_rgba(0,0,0,0.06),0_1px_3px_rgba(0,0,0,0.03)] border border-white flex items-center justify-between gap-4">
            {/* Logo: Nirikshan eye/iris symbol and title */}
            <Link to="/" className="flex items-center gap-2.5 group">
              <svg
                className="w-5 h-5 text-[#7B24E7] group-hover:scale-110 transition-transform"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
              >
                <circle cx="12" cy="12" r="9" />
                <circle cx="12" cy="12" r="3.5" fill="currentColor" />
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
              className="px-5 py-2 rounded-full bg-[#7B24E7] hover:bg-[#6A1BD6] active:bg-[#5815B6] text-white text-xs sm:text-[13px] font-semibold shadow-[0_2px_12px_rgba(123,36,231,0.35)] hover:shadow-[0_4px_16px_rgba(123,36,231,0.45)] transition-all shrink-0 flex items-center gap-1.5 cursor-pointer"
            >
              <span>Open workspace</span>
              <span className="text-sm font-normal">→</span>
            </button>
          </nav>
        </header>

        {/* 4. Hero Content: Two Columns, Vertically Centered */}
        <div className="relative z-20 flex-1 flex items-center max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-center w-full">
            {/* Left Column: Pill badge, headline with white gradient, subtext, and CTA buttons */}
            <div className="lg:col-span-6 xl:col-span-5 flex flex-col items-start text-left z-20 relative">
              {/* Soft luminous white gradient glow behind the sentence */}
              <div
                className="absolute -top-16 -left-16 w-[560px] h-[480px] rounded-full pointer-events-none"
                style={{
                  background:
                    'radial-gradient(ellipse 65% 55% at 40% 45%, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.70) 42%, rgba(255, 255, 255, 0.25) 68%, transparent 85%)',
                  filter: 'blur(22px)',
                  zIndex: -1,
                }}
              />

              {/* Pill badge above headline */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-white/85 backdrop-blur-md border border-white/80 shadow-[0_2px_8px_rgba(0,0,0,0.04)] text-[#7C3AED] text-xs font-semibold mb-4">
                <span className="w-1.5 h-1.5 rounded-full bg-[#7C3AED] animate-pulse" />
                <span>SIH 2026 · PS 26261 · AICTE</span>
              </div>

              {/* Bold black headline — clean leading & padding so "its evidence" is never cut */}
              <h1 className="text-4xl sm:text-[46px] lg:text-[50px] xl:text-[54px] font-extrabold text-[#0F172A] tracking-[-0.03em] leading-[1.18] pb-1.5 overflow-visible">
                Every approval,<br />
                checked against<br />
                its evidence.
              </h1>

              {/* 2-line clean subtext */}
              <p className="mt-3.5 text-xs sm:text-[13px] md:text-sm text-stone-600 leading-relaxed font-normal max-w-md">
                Signatures, records and rules, verified at the source.<br />
                Officials decide; Nirikshan shows the proof.
              </p>

              {/* Call to Action: Solid purple button with arrow & white outlined button */}
              <div className="mt-6 flex flex-wrap items-center gap-3">
                <button
                  onClick={() => navigate('/workspace')}
                  className="px-5 py-2.5 rounded-full bg-[#7B24E7] hover:bg-[#6A1BD6] active:bg-[#5815B6] text-white text-xs sm:text-[13px] font-semibold shadow-[0_4px_16px_rgba(123,36,231,0.35)] hover:shadow-[0_6px_22px_rgba(123,36,231,0.45)] transition-all flex items-center gap-2 group cursor-pointer"
                >
                  <span>Open the workspace</span>
                  <span className="text-sm group-hover:translate-x-0.5 transition-transform">→</span>
                </button>
                <button
                  onClick={() => scrollToSection('how-it-works')}
                  className="px-5 py-2.5 rounded-full bg-white/50 hover:bg-white text-stone-900 border border-stone-300 shadow-sm hover:shadow-md text-xs sm:text-[13px] font-semibold transition-all backdrop-blur-sm cursor-pointer"
                >
                  See how it works
                </button>
              </div>
            </div>

            {/* Right Column: empty spacer to preserve the two-column layout for the 3D hand sculptures */}
            <div className="lg:col-span-6 xl:col-span-7" aria-hidden="true" />
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
