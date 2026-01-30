"use client";
import React from "react"

export default function TaxWorkflowProgress({ step }: { step: number }) {
  const steps = [
    "Upload Tax Docs",
    "Import/Enter Transactions",
    "Review & Categorize",
    "Personal Tax Info",
    "AI Tax Prep & File"
  ]
  return (
    <div className="flex items-center gap-2 mb-8">
      {steps.map((label, idx) => (
        <React.Fragment key={label}>
          <div className={`rounded-full w-8 h-8 flex items-center justify-center font-bold text-white ${step === idx + 1 ? "bg-blue-700" : "bg-blue-300"}`}>{idx + 1}</div>
          <span className={`text-sm ${step === idx + 1 ? "font-bold text-blue-900" : "text-gray-500"}`}>{label}</span>
          {idx < steps.length - 1 && <span className="w-8 h-1 bg-blue-200 rounded" />}
        </React.Fragment>
      ))}
    </div>
  )
}
