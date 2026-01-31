"use client";

import React, { useState } from "react";
import { FormField as IFormField, FormSection as IFormSection } from "./form-schema";

const glassmorphism = {
  background: "rgba(17, 17, 17, 0.8)",
  backdropFilter: "blur(10px)",
  border: "1px solid rgba(255, 107, 53, 0.2)",
};

interface FormFieldProps {
  field: IFormField;
  value: any;
  onChange: (value: any) => void;
  error?: string;
  visible?: boolean;
}

export const FormFieldComponent: React.FC<FormFieldProps> = ({
  field,
  value,
  onChange,
  error,
  visible = true,
}) => {
  if (!visible) return null;

  const commonInputStyle = {
    width: "100%",
    padding: "12px",
    background: "rgba(10, 10, 10, 0.9)",
    color: "#f7f6f3",
    border: `1px solid ${error ? "rgba(196, 30, 58, 0.5)" : "rgba(255, 107, 53, 0.3)"}`,
    fontSize: "14px",
    outline: "none",
    transition: "all 0.2s ease",
  };

  const gridSpan = field.gridColumns === 2 ? { gridColumn: "1 / -1" } : {};

  return (
    <div style={{ marginBottom: "1rem", ...gridSpan }}>
      <label style={{ display: "block", fontSize: "12px", color: "#888", marginBottom: "6px", fontWeight: 600 }}>
        {field.label}
        {field.required && <span style={{ color: "#ff6b7a" }}> *</span>}
        {field.nemsisElement && <span style={{ color: "#666", fontSize: "10px", marginLeft: "6px" }}>({field.nemsisElement})</span>}
      </label>

      {field.type === "text" || field.type === "number" || field.type === "date" || field.type === "time" || field.type === "datetime" ? (
        <input
          type={field.type === "datetime" ? "datetime-local" : field.type}
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          min={field.validation?.min}
          max={field.validation?.max}
          style={commonInputStyle as React.CSSProperties}
          onFocus={(e) => {
            (e.target as HTMLInputElement).style.borderColor = "rgba(255, 107, 53, 0.6)";
          }}
          onBlur={(e) => {
            (e.target as HTMLInputElement).style.borderColor = error
              ? "rgba(196, 30, 58, 0.5)"
              : "rgba(255, 107, 53, 0.3)";
          }}
        />
      ) : field.type === "ssn" ? (
        <input
          type="text"
          value={value || ""}
          onChange={(e) => {
            let val = e.target.value.replace(/\D/g, "");
            if (val.length > 3 && val.length <= 5) val = val.slice(0, 3) + "-" + val.slice(3);
            else if (val.length > 5) val = val.slice(0, 3) + "-" + val.slice(3, 5) + "-" + val.slice(5, 9);
            onChange(val);
          }}
          placeholder={field.placeholder || "XXX-XX-XXXX"}
          maxLength={11}
          style={commonInputStyle as React.CSSProperties}
        />
      ) : field.type === "phone" ? (
        <input
          type="tel"
          value={value || ""}
          onChange={(e) => {
            let val = e.target.value.replace(/\D/g, "");
            if (val.length > 3 && val.length <= 6) val = "(" + val.slice(0, 3) + ") " + val.slice(3);
            else if (val.length > 6) val = "(" + val.slice(0, 3) + ") " + val.slice(3, 6) + "-" + val.slice(6, 10);
            onChange(val);
          }}
          placeholder={field.placeholder || "(555) 123-4567"}
          maxLength={14}
          style={commonInputStyle as React.CSSProperties}
        />
      ) : field.type === "textarea" ? (
        <textarea
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          style={{
            ...commonInputStyle,
            minHeight: "100px",
            resize: "vertical",
          } as React.CSSProperties}
          onFocus={(e) => {
            (e.target as HTMLTextAreaElement).style.borderColor = "rgba(255, 107, 53, 0.6)";
          }}
          onBlur={(e) => {
            (e.target as HTMLTextAreaElement).style.borderColor = error
              ? "rgba(196, 30, 58, 0.5)"
              : "rgba(255, 107, 53, 0.3)";
          }}
        />
      ) : field.type === "select" ? (
        <select
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          style={commonInputStyle as React.CSSProperties}
        >
          <option value="">Select {field.label}</option>
          {field.options?.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : field.type === "voice" ? (
        <VoiceInputComponent value={value} onChange={onChange} />
      ) : field.type === "ocr" ? (
        <OcrInputComponent value={value} onChange={onChange} field={field} />
      ) : field.type === "vitals-row" ? (
        <VitalsRowComponent value={value} onChange={onChange} />
      ) : field.type === "medication-row" ? (
        <MedicationRowComponent value={value} onChange={onChange} />
      ) : field.type === "procedure-row" ? (
        <ProcedureRowComponent value={value} onChange={onChange} />
      ) : field.type === "signature" ? (
        <SignatureComponent value={value} onChange={onChange} label={field.label} />
      ) : null}

      {field.quickPicks && field.quickPicks.length > 0 && (
        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
          {field.quickPicks.map((pick) => (
            <button
              key={pick}
              type="button"
              onClick={() => onChange(value ? value + ", " + pick : pick)}
              style={{
                padding: "4px 8px",
                background: "rgba(255, 107, 53, 0.1)",
                border: "1px solid rgba(255, 107, 53, 0.3)",
                color: "#ff6b35",
                fontSize: "11px",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              + {pick}
            </button>
          ))}
        </div>
      )}

      {error && <div style={{ fontSize: "12px", color: "#ff6b7a", marginTop: "4px" }}>⚠ {error}</div>}
    </div>
  );
};

const VoiceInputComponent: React.FC<{ value: any; onChange: (v: any) => void }> = ({ value, onChange }) => {
  const [recording, setRecording] = useState(false);

  return (
    <button
      type="button"
      onClick={() => setRecording(!recording)}
      style={{
        width: "100%",
        padding: "12px",
        background: recording ? "rgba(196, 30, 58, 0.2)" : "rgba(255, 107, 53, 0.1)",
        border: `1px solid ${recording ? "rgba(196, 30, 58, 0.5)" : "rgba(255, 107, 53, 0.3)"}`,
        color: recording ? "#ff6b7a" : "#ff6b35",
        fontWeight: 600,
        cursor: "pointer",
        fontSize: "14px",
        transition: "all 0.2s ease",
      }}
    >
      {recording ? "🔴 Recording..." : "🎙️ Record Narrative"}
    </button>
  );
};

const OcrInputComponent: React.FC<{ value: any; onChange: (v: any) => void; field: IFormField }> = ({
  value,
  onChange,
  field,
}) => {
  return (
    <button
      type="button"
      style={{
        width: "100%",
        padding: "12px",
        background: "rgba(255, 107, 53, 0.1)",
        border: "1px solid rgba(255, 107, 53, 0.3)",
        color: "#ff6b35",
        fontWeight: 600,
        cursor: "pointer",
        fontSize: "14px",
        transition: "all 0.2s ease",
      }}
    >
      📷 {field.label}
    </button>
  );
};

const VitalsRowComponent: React.FC<{ value: any; onChange: (v: any) => void }> = ({ value = [], onChange }) => {
  const [vitals, setVitals] = useState(value || []);

  const addVitalSet = () => {
    const newSet = {
      timestamp: new Date().toISOString(),
      hr: "",
      sbp: "",
      dbp: "",
      rr: "",
      spo2: "",
      temp: "",
      glucose: "",
      etco2: "",
      gcs: "",
    };
    const updated = [...vitals, newSet];
    setVitals(updated);
    onChange(updated);
  };

  const updateVital = (index: number, field: string, val: string) => {
    const updated = [...vitals];
    updated[index][field] = val;
    setVitals(updated);
    onChange(updated);
  };

  const removeVital = (index: number) => {
    const updated = vitals.filter((_: any, i: number) => i !== index);
    setVitals(updated);
    onChange(updated);
  };

  return (
    <div>
      <button
        type="button"
        onClick={addVitalSet}
        style={{
          width: "100%",
          padding: "12px",
          background: "rgba(255, 107, 53, 0.1)",
          border: "1px solid rgba(255, 107, 53, 0.3)",
          color: "#ff6b35",
          fontWeight: 600,
          cursor: "pointer",
          fontSize: "14px",
          marginBottom: "1rem",
        }}
      >
        + Add Vital Signs
      </button>

      {vitals.map((vital: any, idx: number) => (
        <div
          key={`vital-${vital.timestamp || idx}`}
          style={{
            background: "rgba(10, 10, 10, 0.6)",
            border: "1px solid rgba(255, 107, 53, 0.2)",
            padding: "1rem",
            marginBottom: "1rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
            <span style={{ fontSize: "12px", color: "#888", fontWeight: 600 }}>
              Vitals #{idx + 1} - {new Date(vital.timestamp).toLocaleTimeString()}
            </span>
            <button
              type="button"
              onClick={() => removeVital(idx)}
              style={{
                background: "transparent",
                border: "none",
                color: "#ff6b7a",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: 700,
              }}
            >
              Remove
            </button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.75rem" }}>
            <input
              type="number"
              placeholder="HR"
              value={vital.hr}
              onChange={(e) => updateVital(idx, "hr", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
            <input
              type="number"
              placeholder="SBP"
              value={vital.sbp}
              onChange={(e) => updateVital(idx, "sbp", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
            <input
              type="number"
              placeholder="DBP"
              value={vital.dbp}
              onChange={(e) => updateVital(idx, "dbp", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
            <input
              type="number"
              placeholder="RR"
              value={vital.rr}
              onChange={(e) => updateVital(idx, "rr", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
            <input
              type="number"
              placeholder="SpO2"
              value={vital.spo2}
              onChange={(e) => updateVital(idx, "spo2", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
            <input
              type="number"
              placeholder="Temp (°F)"
              value={vital.temp}
              onChange={(e) => updateVital(idx, "temp", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
            <input
              type="number"
              placeholder="Glucose"
              value={vital.glucose}
              onChange={(e) => updateVital(idx, "glucose", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
            <input
              type="number"
              placeholder="EtCO2"
              value={vital.etco2}
              onChange={(e) => updateVital(idx, "etco2", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

const MedicationRowComponent: React.FC<{ value: any; onChange: (v: any) => void }> = ({ value = [], onChange }) => {
  const [medications, setMedications] = useState(value || []);

  const addMedication = () => {
    const newMed = {
      timestamp: new Date().toISOString(),
      name: "",
      dose: "",
      units: "",
      route: "",
      provider: "",
    };
    const updated = [...medications, newMed];
    setMedications(updated);
    onChange(updated);
  };

  const updateMedication = (index: number, field: string, val: string) => {
    const updated = [...medications];
    updated[index][field] = val;
    setMedications(updated);
    onChange(updated);
  };

  const removeMedication = (index: number) => {
    const updated = medications.filter((_: any, i: number) => i !== index);
    setMedications(updated);
    onChange(updated);
  };

  return (
    <div>
      <button
        type="button"
        onClick={addMedication}
        style={{
          width: "100%",
          padding: "12px",
          background: "rgba(255, 107, 53, 0.1)",
          border: "1px solid rgba(255, 107, 53, 0.3)",
          color: "#ff6b35",
          fontWeight: 600,
          cursor: "pointer",
          fontSize: "14px",
          marginBottom: "1rem",
        }}
      >
        + Add Medication
      </button>

      {medications.map((med: any, idx: number) => (
        <div
          key={`medication-${med.timestamp || idx}`}
          style={{
            background: "rgba(10, 10, 10, 0.6)",
            border: "1px solid rgba(255, 107, 53, 0.2)",
            padding: "1rem",
            marginBottom: "1rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
            <span style={{ fontSize: "12px", color: "#888", fontWeight: 600 }}>
              Medication #{idx + 1} - {new Date(med.timestamp).toLocaleTimeString()}
            </span>
            <button
              type="button"
              onClick={() => removeMedication(idx)}
              style={{
                background: "transparent",
                border: "none",
                color: "#ff6b7a",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: 700,
              }}
            >
              Remove
            </button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: "0.75rem" }}>
            <input
              type="text"
              placeholder="Medication Name"
              value={med.name}
              onChange={(e) => updateMedication(idx, "name", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
            <input
              type="text"
              placeholder="Dose"
              value={med.dose}
              onChange={(e) => updateMedication(idx, "dose", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
            <input
              type="text"
              placeholder="Units"
              value={med.units}
              onChange={(e) => updateMedication(idx, "units", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
            <select
              value={med.route}
              onChange={(e) => updateMedication(idx, "route", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            >
              <option value="">Route</option>
              <option value="IV">IV</option>
              <option value="IO">IO</option>
              <option value="IM">IM</option>
              <option value="PO">PO</option>
              <option value="SL">SL</option>
              <option value="Inhaled">Inhaled</option>
              <option value="Topical">Topical</option>
            </select>
          </div>
        </div>
      ))}
    </div>
  );
};

const ProcedureRowComponent: React.FC<{ value: any; onChange: (v: any) => void }> = ({ value = [], onChange }) => {
  const [procedures, setProcedures] = useState(value || []);

  const addProcedure = () => {
    const newProc = {
      timestamp: new Date().toISOString(),
      type: "",
      location: "",
      success: "yes",
      provider: "",
      notes: "",
    };
    const updated = [...procedures, newProc];
    setProcedures(updated);
    onChange(updated);
  };

  const updateProcedure = (index: number, field: string, val: string) => {
    const updated = [...procedures];
    updated[index][field] = val;
    setProcedures(updated);
    onChange(updated);
  };

  const removeProcedure = (index: number) => {
    const updated = procedures.filter((_: any, i: number) => i !== index);
    setProcedures(updated);
    onChange(updated);
  };

  return (
    <div>
      <button
        type="button"
        onClick={addProcedure}
        style={{
          width: "100%",
          padding: "12px",
          background: "rgba(255, 107, 53, 0.1)",
          border: "1px solid rgba(255, 107, 53, 0.3)",
          color: "#ff6b35",
          fontWeight: 600,
          cursor: "pointer",
          fontSize: "14px",
          marginBottom: "1rem",
        }}
      >
        + Add Procedure
      </button>

      {procedures.map((proc: any, idx: number) => (
        <div
          key={`procedure-${proc.timestamp || idx}`}
          style={{
            background: "rgba(10, 10, 10, 0.6)",
            border: "1px solid rgba(255, 107, 53, 0.2)",
            padding: "1rem",
            marginBottom: "1rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
            <span style={{ fontSize: "12px", color: "#888", fontWeight: 600 }}>
              Procedure #{idx + 1} - {new Date(proc.timestamp).toLocaleTimeString()}
            </span>
            <button
              type="button"
              onClick={() => removeProcedure(idx)}
              style={{
                background: "transparent",
                border: "none",
                color: "#ff6b7a",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: 700,
              }}
            >
              Remove
            </button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 2fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <select
              value={proc.type}
              onChange={(e) => updateProcedure(idx, "type", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            >
              <option value="">Procedure Type</option>
              <option value="IV Access">IV Access</option>
              <option value="IO Access">IO Access</option>
              <option value="Intubation">Intubation</option>
              <option value="Needle Decompression">Needle Decompression</option>
              <option value="Chest Tube">Chest Tube</option>
              <option value="12-Lead ECG">12-Lead ECG</option>
              <option value="Oxygen Administration">Oxygen Administration</option>
              <option value="CPR">CPR</option>
              <option value="Defibrillation">Defibrillation</option>
              <option value="Cardioversion">Cardioversion</option>
              <option value="Splinting">Splinting</option>
              <option value="Bleeding Control">Bleeding Control</option>
            </select>
            <input
              type="text"
              placeholder="Location/Details"
              value={proc.location}
              onChange={(e) => updateProcedure(idx, "location", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            />
            <select
              value={proc.success}
              onChange={(e) => updateProcedure(idx, "success", e.target.value)}
              style={{
                padding: "8px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 107, 53, 0.2)",
                color: "#f7f6f3",
                fontSize: "13px",
              }}
            >
              <option value="yes">Success</option>
              <option value="no">Failed</option>
            </select>
          </div>
          <textarea
            placeholder="Additional notes..."
            value={proc.notes}
            onChange={(e) => updateProcedure(idx, "notes", e.target.value)}
            style={{
              width: "100%",
              padding: "8px",
              background: "rgba(0, 0, 0, 0.5)",
              border: "1px solid rgba(255, 107, 53, 0.2)",
              color: "#f7f6f3",
              fontSize: "13px",
              minHeight: "60px",
              resize: "vertical",
            }}
          />
        </div>
      ))}
    </div>
  );
};

const SignatureComponent: React.FC<{ value: any; onChange: (v: any) => void; label: string }> = ({ value, onChange, label }) => {
  const [signed, setSigned] = useState(!!value);

  const handleSign = () => {
    const timestamp = new Date().toISOString();
    onChange({ signed: true, timestamp });
    setSigned(true);
  };

  return (
    <div>
      {!signed ? (
        <button
          type="button"
          onClick={handleSign}
          style={{
            width: "100%",
            padding: "12px",
            background: "rgba(255, 107, 53, 0.1)",
            border: "1px solid rgba(255, 107, 53, 0.3)",
            color: "#ff6b35",
            fontWeight: 600,
            cursor: "pointer",
            fontSize: "14px",
          }}
        >
          ✍️ Sign {label}
        </button>
      ) : (
        <div
          style={{
            padding: "12px",
            background: "rgba(111, 201, 111, 0.1)",
            border: "1px solid rgba(111, 201, 111, 0.3)",
            color: "#6fc96f",
            fontSize: "14px",
          }}
        >
          ✓ Signed on {new Date(value.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  );
};

interface FormSectionProps {
  section: IFormSection;
  values: Record<string, any>;
  onChange: (field: string, value: any) => void;
  errors: Record<string, string>;
  expanded: boolean;
  onToggle: () => void;
}

export const FormSectionComponent: React.FC<FormSectionProps> = ({
  section,
  values,
  onChange,
  errors,
  expanded,
  onToggle,
}) => {
  return (
    <div style={{ ...glassmorphism, marginBottom: "1rem", overflow: "hidden" }}>
      <button
        type="button"
        onClick={onToggle}
        style={{
          width: "100%",
          background: "transparent",
          border: "none",
          padding: "1.5rem",
          color: "#ff6b35",
          fontSize: "16px",
          fontWeight: 700,
          textAlign: "left",
          cursor: "pointer",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          {section.title}
          {section.nemsisSection && <span style={{ color: "#666", fontSize: "12px", marginLeft: "8px" }}>({section.nemsisSection})</span>}
        </div>
        <span style={{ fontSize: "20px" }}>{expanded ? "−" : "+"}</span>
      </button>

      {expanded && (
        <div style={{ padding: "0 1.5rem 1.5rem 1.5rem", borderTop: "1px solid rgba(255, 107, 53, 0.1)" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            {section.fields.map((field) => (
              <FormFieldComponent
                key={field.id}
                field={field}
                value={values[field.id]}
                onChange={(v) => onChange(field.id, v)}
                error={errors[field.id]}
                visible={!field.visibility || field.visibility.condition(values[field.visibility.dependsOn])}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

interface ValidationErrorsProps {
  errors: string[];
}

export const ValidationErrorsComponent: React.FC<ValidationErrorsProps> = ({ errors }) => {
  if (errors.length === 0) return null;

  return (
    <div
      style={{
        ...glassmorphism,
        borderColor: "rgba(196, 30, 58, 0.5)",
        padding: "1rem",
        marginBottom: "1.5rem",
      }}
    >
      {errors.map((err, idx) => (
        <div key={`error-${idx}-${err.slice(0, 20)}`} style={{ fontSize: "12px", color: "#ff6b7a", marginBottom: "4px" }}>
          ⚠ {err}
        </div>
      ))}
    </div>
  );
};

interface StatusBarProps {
  isOnline: boolean;
  pendingCount: number;
  variant: string;
}

export const StatusBarComponent: React.FC<StatusBarProps> = ({ isOnline, pendingCount, variant }) => {
  const [autoSaveStatus, setAutoSaveStatus] = useState<string>("Saved");

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "2rem",
        position: "sticky" as const,
        top: 0,
        background: "linear-gradient(135deg, #000000 0%, #0a0a0a 100%)",
        paddingTop: "1rem",
        zIndex: 10,
      }}
    >
      <div>
        <h1 style={{ margin: 0, fontSize: "1.8rem", fontWeight: 800, color: "#ff6b35" }}>
          {variant} ePCR
        </h1>
        <p style={{ margin: "0.25rem 0 0 0", fontSize: "12px", color: "#888" }}>
          Patient Care Report • NEMSIS v3.5 Compliant
        </p>
      </div>
      <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
        <div style={{ fontSize: "11px", color: "#6fc96f" }}>
          {autoSaveStatus}
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <div
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              background: isOnline ? "#6fc96f" : "#ff4d4f",
            }}
          />
          <span style={{ fontSize: "11px", color: isOnline ? "#6fc96f" : "#ff4d4f" }}>
            {isOnline ? "Online" : "Offline"}
          </span>
        </div>
        {pendingCount > 0 && (
          <div style={{ fontSize: "11px", color: "#ff6b35" }}>
            {pendingCount} pending
          </div>
        )}
      </div>
    </div>
  );
};
