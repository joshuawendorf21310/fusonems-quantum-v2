"use client";

import { useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";

export type CodeSet = "icd10" | "snomed" | "rxnorm";

export interface Suggestion {
  code: string;
  description: string;
  nemsis_element_ref?: string | null;
}

export interface TerminologySuggestResponse {
  suggestions: Suggestion[];
  explanation?: string | null;
  ai_available?: boolean;
}

interface TerminologySuggestProps {
  /** Current text (e.g. chief complaint) to suggest codes for */
  query: string;
  /** Code set: icd10 (diagnosis), snomed, rxnorm */
  codeSet?: CodeSet;
  /** Called when user picks a suggestion */
  onSelect?: (code: string, description: string) => void;
  /** Optional: controlled code/description to show as selected */
  selectedCode?: string;
  selectedDescription?: string;
  /** Input placeholder */
  placeholder?: string;
  /** Label above the suggest button */
  label?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Class name for container */
  className?: string;
}

export function TerminologySuggest({
  query,
  codeSet = "icd10",
  onSelect,
  selectedCode,
  selectedDescription,
  placeholder = "e.g., Chest pain, Difficulty breathing",
  label = "Suggest ICD-10 codes",
  disabled = false,
  className = "",
}: TerminologySuggestProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  const fetchSuggestions = useCallback(async () => {
    const q = (typeof query === "string" ? query : "").trim();
    if (!q) {
      setSuggestions([]);
      setExplanation("Enter chief complaint or description first.");
      setOpen(true);
      return;
    }
    setLoading(true);
    setExplanation(null);
    setSuggestions([]);
    try {
      const res = await apiFetch<TerminologySuggestResponse>("/api/epcr/terminology/suggest", {
        method: "POST",
        body: JSON.stringify({ query: q, code_set: codeSet }),
      });
      setSuggestions(res?.suggestions ?? []);
      setExplanation(res?.explanation ?? null);
      setOpen(true);
    } catch (e) {
      setExplanation("Could not load suggestions. Check backend and Ollama.");
      setOpen(true);
    } finally {
      setLoading(false);
    }
  }, [query, codeSet]);

  const handleSelect = (s: Suggestion) => {
    onSelect?.(s.code, s.description);
    setOpen(false);
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {label && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-zinc-400">{label}</span>
          <button
            type="button"
            onClick={fetchSuggestions}
            disabled={disabled || loading}
            className="px-3 py-1.5 rounded-lg bg-orange-600/20 text-orange-400 hover:bg-orange-600/30 text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Loading…" : "Suggest codes"}
          </button>
        </div>
      )}
      {(selectedCode || selectedDescription) && (
        <div className="text-sm text-zinc-300">
          {selectedCode && <span className="font-mono text-orange-400">{selectedCode}</span>}
          {selectedCode && selectedDescription && " — "}
          {selectedDescription}
        </div>
      )}
      {open && (suggestions.length > 0 || explanation) && (
        <div className="rounded-lg border border-zinc-700 bg-zinc-900/95 p-3 space-y-2 max-h-48 overflow-auto">
          {explanation && <p className="text-xs text-zinc-500">{explanation}</p>}
          <ul className="space-y-1">
            {suggestions.map((s, i) => (
              <li key={`${s.code}-${i}`}>
                <button
                  type="button"
                  onClick={() => handleSelect(s)}
                  className="w-full text-left px-2 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-sm"
                >
                  <span className="font-mono text-orange-400">{s.code}</span>
                  {" — "}
                  {s.description}
                </button>
              </li>
            ))}
          </ul>
          {suggestions.length === 0 && explanation && (
            <p className="text-sm text-zinc-400">No codes returned. Add manually or try different wording.</p>
          )}
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="text-xs text-zinc-500 hover:text-zinc-400"
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
}
