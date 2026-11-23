import React, { useContext, useEffect, useId, useRef, useState } from "react";
import { Accessibility } from "lucide-react";
import { Link } from "react-router-dom";
import { useT } from "../i18n";
import { ThemeContext } from "../context/ThemeContext";
import { cn } from "../ui";
import { useDisplayPrefs, type Contrast, type TextSize } from "./prefs";

export function AccessibilityMenu({
  withTheme = false,
  className,
}: {
  withTheme?: boolean;
  className?: string;
}) {
  const t = useT();
  const { textSize, setTextSize, contrast, setContrast } = useDisplayPrefs();
  const themeContext = useContext(ThemeContext);
  const theme = themeContext?.theme || "light";
  const toggleTheme = themeContext?.toggleTheme || (() => {});

  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const btn = useRef<HTMLButtonElement>(null);
  const panelId = useId();

  useEffect(() => {
    if (!open) return;
    const onDown = (e: PointerEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        btn.current?.focus();
      }
    };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const label = t("Accessibility options");

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        ref={btn}
        type="button"
        aria-label={label}
        aria-expanded={open}
        aria-controls={open ? panelId : undefined}
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "grid size-9 place-items-center rounded-full text-ink-3 transition-colors hover:bg-surface-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-brand-500 cursor-pointer",
          open && "bg-surface-2 text-ink"
        )}
      >
        <Accessibility className="size-4" aria-hidden />
      </button>

      {open && (
        <div
          id={panelId}
          role="group"
          aria-label={label}
          className="absolute top-11 right-0 z-50 w-72 rounded-2xl border border-line bg-surface p-4 shadow-xl"
        >
          <div className="space-y-4">
            <div>
              <p className="mb-1.5 text-xs font-semibold text-ink-3">{t("Text size")}</p>
              <div className="flex rounded-xl bg-surface-2 p-1 border border-line">
                <button
                  type="button"
                  onClick={() => setTextSize("sm")}
                  className={cn(
                    "flex-1 rounded-lg py-1 text-xs font-medium transition-colors cursor-pointer",
                    textSize === "sm" ? "bg-surface text-brand-600 shadow-xs" : "text-ink-3 hover:text-ink"
                  )}
                >
                  <span className="font-semibold">A-</span>
                  <span className="sr-only"> smaller</span>
                </button>
                <button
                  type="button"
                  onClick={() => setTextSize("md")}
                  className={cn(
                    "flex-1 rounded-lg py-1 text-xs font-medium transition-colors cursor-pointer",
                    textSize === "md" ? "bg-surface text-brand-600 shadow-xs" : "text-ink-3 hover:text-ink"
                  )}
                >
                  <span className="font-semibold">A</span>
                  <span className="sr-only"> default</span>
                </button>
                <button
                  type="button"
                  onClick={() => setTextSize("lg")}
                  className={cn(
                    "flex-1 rounded-lg py-1 text-xs font-medium transition-colors cursor-pointer",
                    textSize === "lg" ? "bg-surface text-brand-600 shadow-xs" : "text-ink-3 hover:text-ink"
                  )}
                >
                  <span className="font-semibold">A+</span>
                  <span className="sr-only"> larger</span>
                </button>
              </div>
            </div>

            <div>
              <p className="mb-1.5 text-xs font-semibold text-ink-3">{t("Contrast")}</p>
              <div className="flex rounded-xl bg-surface-2 p-1 border border-line">
                <button
                  type="button"
                  onClick={() => setContrast("standard")}
                  className={cn(
                    "flex-1 rounded-lg py-1 text-xs font-medium transition-colors cursor-pointer",
                    contrast === "standard" ? "bg-surface text-brand-600 shadow-xs" : "text-ink-3 hover:text-ink"
                  )}
                >
                  Standard
                </button>
                <button
                  type="button"
                  onClick={() => setContrast("high")}
                  className={cn(
                    "flex-1 rounded-lg py-1 text-xs font-medium transition-colors cursor-pointer",
                    contrast === "high" ? "bg-surface text-brand-600 shadow-xs" : "text-ink-3 hover:text-ink"
                  )}
                >
                  High contrast
                </button>
              </div>
            </div>

            {withTheme && (
              <div>
                <p className="mb-1.5 text-xs font-semibold text-ink-3">{t("Theme")}</p>
                <div className="flex rounded-xl bg-surface-2 p-1 border border-line">
                  <button
                    type="button"
                    onClick={() => theme !== "light" && toggleTheme()}
                    className={cn(
                      "flex-1 rounded-lg py-1 text-xs font-medium transition-colors cursor-pointer",
                      theme === "light" ? "bg-surface text-brand-600 shadow-xs" : "text-ink-3 hover:text-ink"
                    )}
                  >
                    Light
                  </button>
                  <button
                    type="button"
                    onClick={() => theme !== "dark" && toggleTheme()}
                    className={cn(
                      "flex-1 rounded-lg py-1 text-xs font-medium transition-colors cursor-pointer",
                      theme === "dark" ? "bg-surface text-brand-600 shadow-xs" : "text-ink-3 hover:text-ink"
                    )}
                  >
                    Dark
                  </button>
                </div>
              </div>
            )}

            <p className="border-t border-line pt-3 text-xs">
              <Link
                to="/accessibility"
                className="text-brand-600 hover:text-brand-700 underline underline-offset-2"
                onClick={() => setOpen(false)}
              >
                {t("Accessibility statement")}
              </Link>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
