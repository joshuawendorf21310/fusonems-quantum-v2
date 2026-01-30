"use client";

import { UniversalEpcrForm } from "@/lib/epcr/form-renderer";
import { hemsSchema } from "@/lib/epcr/form-schema";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

function mapFormDataToQuickPCR(data: Record<string, unknown>) {
  const str = (v: unknown) => (v != null ? String(v) : "");
  return {
    incident_number: str(data.incident_number) || `INC-${new Date().toISOString().slice(0, 19).replace(/[-:T]/g, "").slice(0, 14)}`,
    patient_first_name: str(data.first_name),
    patient_last_name: str(data.last_name),
    patient_dob: str(data.date_of_birth),
    patient_gender: str(data.gender),
    patient_age: data.age != null ? str(data.age) : "",
    chief_complaint: str(data.chief_complaint),
    narrative: str(data.narrative),
    destination_facility: str(data.destination_facility ?? data.patient_destination),
    custom_fields: typeof data.custom_fields === "object" && data.custom_fields !== null ? (data.custom_fields as Record<string, unknown>) : {},
  };
}

export default function HemsEpcrCreatePage() {
  const router = useRouter();

  return (
    <UniversalEpcrForm
      schema={hemsSchema}
      onCancel={() => router.back()}
      onSubmit={async (data) => {
        const payload = mapFormDataToQuickPCR(data as Record<string, unknown>);
        const res = await apiFetch<{ record_id: number }>("/api/epcr/pcrs", { method: "POST", body: JSON.stringify(payload) });
        router.push(`/epcr/${res.record_id}`);
      }}
    />
  );
}
