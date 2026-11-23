import React, { forwardRef } from "react";
import { LoaderCircle } from "lucide-react";

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(" ");
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: "sm" | "md" | "lg";
  variant?: "primary" | "secondary" | "ghost" | "outline";
  loading?: boolean;
  leadingIcon?: React.ReactNode;
  trailingIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      size = "md",
      variant = "primary",
      loading = false,
      leadingIcon,
      trailingIcon,
      children,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const sizeClasses = {
      sm: "px-3 py-1.5 text-xs rounded-lg gap-1.5",
      md: "px-4 py-2 text-sm rounded-xl gap-2",
      lg: "px-5 py-3 text-sm font-semibold rounded-xl gap-2.5",
    }[size];

    const variantClasses = {
      primary:
        "bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white shadow-xs focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500",
      secondary:
        "bg-surface-2 hover:bg-surface-3 text-ink border border-line",
      outline:
        "border border-line hover:border-brand-300 hover:bg-brand-50/50 text-ink",
      ghost:
        "hover:bg-surface-2 text-ink-2 hover:text-ink",
    }[variant];

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer",
          sizeClasses,
          variantClasses,
          className
        )}
        {...props}
      >
        {loading ? (
          <LoaderCircle className="size-4 animate-spin text-current" />
        ) : leadingIcon ? (
          <span className="shrink-0">{leadingIcon}</span>
        ) : null}
        <span>{children}</span>
        {!loading && trailingIcon && <span className="shrink-0">{trailingIcon}</span>}
      </button>
    );
  }
);
Button.displayName = "Button";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  leadingIcon?: React.ReactNode;
  trailingIcon?: React.ReactNode;
  inputSize?: "sm" | "md" | "lg";
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ leadingIcon, trailingIcon, inputSize = "md", className, ...props }, ref) => {
    const sizeClasses = {
      sm: "h-9 px-3 text-xs",
      md: "h-10 px-3.5 text-sm",
      lg: "h-12 px-4 text-[0.9375rem]",
    }[inputSize];

    return (
      <div className="relative flex w-full items-center">
        {leadingIcon && (
          <span className="pointer-events-none absolute left-3.5 flex items-center text-ink-3 [&>svg]:size-4">
            {leadingIcon}
          </span>
        )}
        <input
          ref={ref}
          className={cn(
            "w-full rounded-xl border border-line bg-surface text-ink placeholder:text-ink-4 transition-[border-color,box-shadow] duration-150 focus:border-brand-500 focus:ring-3 focus:ring-brand-500/15 focus:outline-none disabled:opacity-50",
            sizeClasses,
            leadingIcon && "pl-10",
            trailingIcon && "pr-10",
            className
          )}
          {...props}
        />
        {trailingIcon && (
          <span className="pointer-events-none absolute right-3.5 flex items-center text-ink-3 [&>svg]:size-4">
            {trailingIcon}
          </span>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export function Field({
  label,
  children,
  error,
  className,
}: {
  label: string;
  children: React.ReactNode;
  error?: string;
  className?: string;
}) {
  return (
    <div className={cn("w-full space-y-1.5", className)}>
      <label className="block text-[0.8125rem] font-semibold text-ink-2">{label}</label>
      {children}
      {error && <p className="text-xs text-mismatch-fg">{error}</p>}
    </div>
  );
}

export function Tag({
  variant = "default",
  children,
  className,
}: {
  variant?: "default" | "demo" | "verified" | "error";
  children: React.ReactNode;
  className?: string;
}) {
  const variantClasses = {
    default: "bg-surface-2 text-ink-2 border-line",
    demo: "bg-brand-50 text-brand-700 border-brand-200",
    verified: "bg-emerald-50 text-emerald-700 border-emerald-200",
    error: "bg-mismatch-bg text-mismatch-fg border-rose-200",
  }[variant];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[0.6875rem] font-semibold uppercase tracking-wider",
        variantClasses,
        className
      )}
    >
      {children}
    </span>
  );
}
