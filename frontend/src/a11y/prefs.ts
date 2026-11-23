import { useEffect, useState } from "react";

export type TextSize = "sm" | "md" | "lg";
export type Contrast = "standard" | "high";

export function useDisplayPrefs() {
  const [textSize, setTextSize] = useState<TextSize>(() => {
    return (localStorage.getItem("a11y_text_size") as TextSize) || "md";
  });

  const [contrast, setContrast] = useState<Contrast>(() => {
    return (localStorage.getItem("a11y_contrast") as Contrast) || "standard";
  });

  useEffect(() => {
    localStorage.setItem("a11y_text_size", textSize);
    const root = document.documentElement;
    root.classList.remove("text-size-sm", "text-size-lg");
    if (textSize === "sm") root.classList.add("text-size-sm");
    if (textSize === "lg") root.classList.add("text-size-lg");
  }, [textSize]);

  useEffect(() => {
    localStorage.setItem("a11y_contrast", contrast);
    const root = document.documentElement;
    if (contrast === "high") {
      root.classList.add("high-contrast");
    } else {
      root.classList.remove("high-contrast");
    }
  }, [contrast]);

  return { textSize, setTextSize, contrast, setContrast };
}
