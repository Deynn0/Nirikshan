import React from 'react';
import { ShieldCheck, Database, FileCheck2, Cpu, AlertTriangle, HelpCircle } from 'lucide-react';

export type TrustLevelType = 
  | 'CRYPTOGRAPHIC_PROOF'
  | 'STATUTORY_DATABASE'
  | 'HARDENED_DOCUMENT'
  | 'MODEL_PREDICTION'
  | 'UNVERIFIED_CLAIM'
  | string;

interface TrustLadderBadgeProps {
  level?: TrustLevelType;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
  isModelAdvisory?: boolean;
}

export const TrustLadderBadge: React.FC<TrustLadderBadgeProps> = ({
  level = 'UNVERIFIED_CLAIM',
  showIcon = true,
  size = 'md',
  isModelAdvisory = false,
}) => {
  const normLevel = level.toUpperCase();

  let bg = 'bg-slate-800 text-slate-300 border-slate-700';
  let label = 'Level 5: Unverified Claim';
  let shortLabel = 'L5 Claim';
  let icon = <HelpCircle className="w-3.5 h-3.5 text-slate-400" />;

  if (normLevel.includes('CRYPTO') || normLevel === 'LEVEL_1') {
    bg = 'bg-purple-950/70 text-purple-200 border-purple-500/40 shadow-sm shadow-purple-900/30';
    label = 'Level 1: Cryptographic Proof (DSig/Merkle)';
    shortLabel = 'L1 Cryptographic';
    icon = <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />;
  } else if (normLevel.includes('STATUTORY') || normLevel === 'LEVEL_2') {
    bg = 'bg-blue-950/70 text-blue-200 border-blue-500/40 shadow-sm shadow-blue-900/30';
    label = 'Level 2: Statutory Database';
    shortLabel = 'L2 Statutory DB';
    icon = <Database className="w-3.5 h-3.5 text-blue-400" />;
  } else if (normLevel.includes('HARDENED') || normLevel === 'LEVEL_3') {
    bg = 'bg-cyan-950/70 text-cyan-200 border-cyan-500/40 shadow-sm shadow-cyan-900/30';
    label = 'Level 3: Hardened Document Forensics';
    shortLabel = 'L3 Forensic Hardened';
    icon = <FileCheck2 className="w-3.5 h-3.5 text-cyan-400" />;
  } else if (normLevel.includes('MODEL') || normLevel === 'LEVEL_4' || isModelAdvisory) {
    bg = 'bg-amber-950/70 text-amber-200 border-amber-500/40 shadow-sm shadow-amber-900/30';
    label = 'Level 4: Model Prediction (Advisory Only)';
    shortLabel = 'L4 Advisory ML';
    icon = <Cpu className="w-3.5 h-3.5 text-amber-400" />;
  } else if (normLevel.includes('UNVERIFIED') || normLevel === 'LEVEL_5') {
    bg = 'bg-rose-950/60 text-rose-300 border-rose-500/30';
    label = 'Level 5: Unverified Claim';
    shortLabel = 'L5 Unverified';
    icon = <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />;
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3 py-1.5 gap-2 font-medium',
  };

  const isModel = normLevel.includes('MODEL') || isModelAdvisory;

  return (
    <div className="inline-flex items-center gap-1.5">
      <span
        title={label}
        className={`inline-flex items-center rounded-md border font-medium transition-all ${bg} ${sizeClasses[size]}`}
      >
        {showIcon && icon}
        <span>{size === 'sm' ? shortLabel : label}</span>
      </span>

      {/* Models ALWAYS labeled Advisory as required by AICTE Scrutiny governance */}
      {isModel && (
        <span className="inline-flex items-center text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
          Advisory
        </span>
      )}
    </div>
  );
};
