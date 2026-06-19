export type Language = "en" | "zh";

export interface LocalizedText {
  en: string;
  zh: string;
}

export const DEFAULT_LANGUAGE: Language = "zh";

export function localized(en: string, zh: string): LocalizedText {
  return { en, zh };
}

export function asLocalizedText(value: string | LocalizedText): LocalizedText {
  if (typeof value !== "string") {
    return value;
  }
  const separator = " / ";
  const index = value.indexOf(separator);
  if (index > 0) {
    return {
      en: value.slice(0, index),
      zh: value.slice(index + separator.length)
    };
  }
  return { en: value, zh: value };
}

export function textFor(
  value: string | LocalizedText,
  language: Language = DEFAULT_LANGUAGE
): string {
  return asLocalizedText(value)[language];
}
