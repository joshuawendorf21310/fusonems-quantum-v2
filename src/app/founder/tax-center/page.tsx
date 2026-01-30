
"use client";
import React, { useState } from "react"
import dynamic from "next/dynamic"
import PersonalTaxForm from "./PersonalTaxForm"
const BankCardImportWidget = dynamic(() => import("@/components/founder/BankCardImportWidget"), { ssr: false })
const SpacesUploadWidget = dynamic(() => import("@/components/founder/SpacesUploadWidget"), { ssr: false })
const TaxWorkflowProgress = dynamic(() => import("@/components/founder/TaxWorkflowProgress"), { ssr: false })

export default function TaxCenter() {
  const [personalTaxData, setPersonalTaxData] = useState<any>(null)
  const [step, setStep] = useState(1)
  const [importedTransactions, setImportedTransactions] = useState<any[]>([])

  const handleTransactionsImported = (txns: any[]) => {
    setImportedTransactions(txns)
    setStep(2)
  }

  const handlePersonalSubmit = (data: any) => {
    setPersonalTaxData(data)
    setStep(3)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-950 to-blue-900 p-8">
      <div className="max-w-3xl mx-auto bg-white rounded-lg shadow-2xl p-8 border border-blue-800">
        <h1 className="text-3xl font-bold text-blue-900 mb-4">Tax Center</h1>
        <p className="mb-6 text-gray-700">Guided Wisconsin EMS/Fire business and personal tax workflow. Review, generate, and e-file your required forms with confidence.</p>
        <TaxWorkflowProgress step={step} />
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2">Upload Tax Documents</h2>
          <div className="flex gap-4">
            <SpacesUploadWidget orgId="demo-org" bucket="business" />
            <SpacesUploadWidget orgId="demo-org" bucket="personal" />
            <SpacesUploadWidget orgId="demo-org" bucket="family" />
          </div>
        </div>
        {step === 1 && (
          <BankCardImportWidget onTransactionsImported={handleTransactionsImported} />
        )}
        {step === 2 && (
          <PersonalTaxForm onSubmit={handlePersonalSubmit} />
        )}
        {step === 3 && (
          <div className="text-green-700 font-bold text-xl text-center p-8">All data saved! (Next steps: AI categorization, review, and tax prep coming soon...)</div>
        )}
      </div>
    </div>
  )
}
