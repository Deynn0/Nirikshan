import React from 'react';

export type PillVariant = 'critical' | 'warning' | 'verified' | 'neutral' | 'violet' | 'blue';

interface PillBadgeProps {
  children: React.ReactNode;
  variant?: PillVariant;
  size?: 'sm' | 'md';
  className?: string;
  dot?: boolean;
}

export const PillBadge: React.FC<PillBadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = '',
  dot = false,
}) => {
  const variantStyles: Record<PillVariant, { bg: string; text: string; border: string; dotColor: string }> = {
    critical: {
      bg: 'bg-rose-50 dark:bg-rose-950/40',
      text: 'text-rose-700 dark:text-rose-300',
      border: 'border-rose-200 dark:border-rose-900/60',
      dotColor: 'bg-rose-500',
    },
    warning: {
      bg: 'bg-amber-50 dark:bg-amber-950/40',
      text: 'text-amber-800 dark:text-amber-300',
      border: 'border-amber-200 dark:border-amber-900/60',
      dotColor: 'bg-amber-500',
    },
    verified: {
      bg: 'bg-emerald-50 dark:bg-emerald-950/40',
      text: 'text-emerald-700 dark:text-emerald-300',
      border: 'border-emerald-200 dark:border-emerald-900/60',
      dotColor: 'bg-emerald-500',
    },
    neutral: {
      bg: 'bg-stone-100 dark:bg-stone-800',
      text: 'text-stone-700 dark:text-stone-300',
      border: 'border-stone-200 dark:border-stone-700',
      dotColor: 'bg-stone-400',
    },
    violet: {
      bg: 'bg-purple-50 dark:bg-purple-950/40',
      text: 'text-purple-700 dark:text-purple-300',
      border: 'border-purple-200 dark:border-purple-900/60',
      dotColor: 'bg-purple-600',
    },
    blue: {
      bg: 'bg-sky-50 dark:bg-sky-950/40',
      text: 'text-sky-700 dark:text-sky-300',
      border: 'border-sky-200 dark:border-sky-900/60',
      dotColor: 'bg-sky-500',
    },
  };

  const current = variantStyles[variant];
  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${current.bg} ${current.text} ${current.border} ${sizeClass} transition-colors ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${current.dotColor} animate-pulse`} />}
      {children}
    </span>
  );
};
