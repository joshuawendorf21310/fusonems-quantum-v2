"use client";

import { useState, useCallback } from "react";
import { Mic, MicOff } from "lucide-react";
import { getVoiceRecorder, isVoiceRecognitionSupported } from "@/lib/voiceToText";

interface NarrativeWithDictationProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  /** When true, dictated text appends to value; when false, replaces. Default true. */
  append?: boolean;
}

export function NarrativeWithDictation({
  value,
  onChange,
  placeholder = "Provide a comprehensive narrative of the call from dispatch to transfer of care...",
  rows = 12,
  required = false,
  disabled = false,
  className = "",
  append = true,
}: NarrativeWithDictationProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState("");
  const [supported] = useState(() => typeof window !== "undefined" && isVoiceRecognitionSupported());

  const handleResult = useCallback(
    (text: string, isFinal: boolean) => {
      if (!isFinal) return;
      setError("");
      if (append && value.trim()) {
        onChange((value.trimEnd() + "\n\n" + text.trim()).trim());
      } else {
        onChange(text.trim());
      }
    },
    [value, onChange, append]
  );

  const handleStart = useCallback(() => {
    if (!supported) {
      setError("Voice recognition not supported in this browser. Use Chrome, Edge, or Safari.");
      return;
    }
    setError("");
    const recorder = getVoiceRecorder();
    recorder.start({
      language: "en-US",
      continuous: true,
      interimResults: true,
      onResult: handleResult,
      onError: (msg) => {
        setError(msg);
        setIsRecording(false);
      },
      onStart: () => setIsRecording(true),
      onEnd: () => setIsRecording(false),
    });
  }, [supported, handleResult]);

  const handleStop = useCallback(() => {
    const recorder = getVoiceRecorder();
    const finalText = recorder.stop();
    if (finalText && append && value.trim()) {
      onChange((value.trimEnd() + "\n\n" + finalText).trim());
    } else if (finalText) {
      onChange(finalText);
    }
    setIsRecording(false);
  }, [value, onChange, append]);

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex gap-2 items-start">
        {supported && (
          <button
            type="button"
            onClick={isRecording ? handleStop : handleStart}
            disabled={disabled}
            className={`shrink-0 p-2.5 rounded-lg transition-colors ${
              isRecording
                ? "bg-red-600 hover:bg-red-700 text-white animate-pulse"
                : "bg-orange-600/20 text-orange-400 hover:bg-orange-600/30 border border-orange-600/30"
            } disabled:opacity-50`}
            title={isRecording ? "Stop dictation" : "Dictate narrative"}
          >
            {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
          </button>
        )}
        <textarea
          name="narrative"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={rows}
          required={required}
          disabled={disabled}
          className="flex-1 w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500 text-zinc-100"
        />
      </div>
      {supported && (
        <p className="text-xs text-zinc-500">
          {isRecording ? "Listening… Speak clearly. Click the mic again to stop." : "Click the microphone to dictate into the narrative."}
        </p>
      )}
      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  );
}
