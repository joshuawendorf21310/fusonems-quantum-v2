// Schema-driven form configuration

export type FieldType = "text" | "number" | "date" | "datetime" | "time" | "textarea" | "select" | "checkbox" | "radio" | "button" | "ocr" | "voice" | "vitals-row" | "medication-row" | "procedure-row" | "signature" | "ssn" | "phone";

export interface FormField {
  id: string;
  type: FieldType;
  label: string;
  placeholder?: string;
  required?: boolean;
  defaultValue?: any;
  nemsisElement?: string; // NEMSIS element ID (e.g., "ePatient.13")
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    custom?: (value: any) => boolean;
  };
  visibility?: {
    dependsOn: string; // field id
    condition: (value: any) => boolean;
  };
  options?: { label: string; value: any }[]; // for select/radio
  aiSuggestion?: {
    protocol?: string[];
    triggers?: string[];
  };
  quickPicks?: any[]; // Quick-pick values for common entries
  gridColumns?: number; // Column span in grid (1-2)
}

export interface FormSection {
  id: string;
  title: string;
  fields: FormField[];
  collapsible?: boolean;
  defaultExpanded?: boolean;
  nemsisSection?: string; // NEMSIS section reference
}

export interface EpcrSchema {
  variant: "EMS" | "FIRE" | "HEMS";
  sections: FormSection[];
  shortcuts?: {
    label: string;
    action: string;
    fields: Record<string, any>;
  }[];
}

// EMS Schema - NEMSIS v3.5 Compliant
export const emsSchema: EpcrSchema = {
  variant: "EMS",
  sections: [
    {
      id: "incident",
      title: "Incident Information",
      nemsisSection: "eDispatch",
      defaultExpanded: true,
      fields: [
        {
          id: "incident_number",
          type: "text",
          label: "Incident Number",
          required: true,
          nemsisElement: "eDispatch.01",
          placeholder: "Auto-populated from CAD",
        },
        {
          id: "dispatch_datetime",
          type: "datetime",
          label: "Dispatch Date/Time",
          required: true,
          nemsisElement: "eDispatch.02",
          gridColumns: 1,
        },
        {
          id: "unit_notified_datetime",
          type: "datetime",
          label: "Unit Notified",
          nemsisElement: "eDispatch.03",
          gridColumns: 1,
        },
        {
          id: "enroute_datetime",
          type: "datetime",
          label: "En Route",
          nemsisElement: "eTimes.05",
          gridColumns: 1,
        },
        {
          id: "scene_arrival_datetime",
          type: "datetime",
          label: "Arrived On Scene",
          required: true,
          nemsisElement: "eTimes.06",
          gridColumns: 1,
        },
        {
          id: "patient_contact_datetime",
          type: "datetime",
          label: "Patient Contact",
          nemsisElement: "eTimes.07",
          gridColumns: 1,
        },
        {
          id: "scene_departure_datetime",
          type: "datetime",
          label: "Left Scene",
          nemsisElement: "eTimes.09",
          gridColumns: 1,
        },
        {
          id: "hospital_arrival_datetime",
          type: "datetime",
          label: "Arrived at Destination",
          nemsisElement: "eTimes.11",
          gridColumns: 1,
        },
        {
          id: "transfer_of_care_datetime",
          type: "datetime",
          label: "Transfer of Care",
          nemsisElement: "eTimes.12",
          gridColumns: 1,
        },
        {
          id: "unit_back_in_service_datetime",
          type: "datetime",
          label: "Back in Service",
          nemsisElement: "eTimes.13",
          gridColumns: 1,
        },
      ],
    },
    {
      id: "patient_demographics",
      title: "Patient Demographics",
      nemsisSection: "ePatient",
      defaultExpanded: true,
      fields: [
        {
          id: "patient_source",
          type: "select",
          label: "Patient Source",
          nemsisElement: "ePatient.15",
          options: [
            { label: "Manual Entry", value: "manual" },
            { label: "Metriport/HIE", value: "metriport" },
            { label: "CAD Import", value: "cad" },
            { label: "Previous ePCR", value: "previous" },
          ],
          gridColumns: 2,
        },
        {
          id: "first_name",
          type: "text",
          label: "First Name",
          required: true,
          nemsisElement: "ePatient.03",
          placeholder: "John",
          gridColumns: 1,
        },
        {
          id: "middle_name",
          type: "text",
          label: "Middle Name",
          nemsisElement: "ePatient.04",
          placeholder: "M",
          gridColumns: 1,
        },
        {
          id: "last_name",
          type: "text",
          label: "Last Name",
          required: true,
          nemsisElement: "ePatient.05",
          placeholder: "Doe",
          gridColumns: 1,
        },
        {
          id: "suffix",
          type: "select",
          label: "Suffix",
          nemsisElement: "ePatient.06",
          options: [
            { label: "None", value: "" },
            { label: "Jr", value: "Jr" },
            { label: "Sr", value: "Sr" },
            { label: "II", value: "II" },
            { label: "III", value: "III" },
            { label: "IV", value: "IV" },
          ],
          gridColumns: 1,
        },
        {
          id: "date_of_birth",
          type: "date",
          label: "Date of Birth",
          required: true,
          nemsisElement: "ePatient.17",
          gridColumns: 1,
        },
        {
          id: "age",
          type: "number",
          label: "Age",
          nemsisElement: "ePatient.15",
          placeholder: "Auto-calculated",
          gridColumns: 1,
        },
        {
          id: "age_units",
          type: "select",
          label: "Age Units",
          nemsisElement: "ePatient.16",
          options: [
            { label: "Years", value: "years" },
            { label: "Months", value: "months" },
            { label: "Days", value: "days" },
            { label: "Hours", value: "hours" },
          ],
          defaultValue: "years",
          gridColumns: 1,
        },
        {
          id: "gender",
          type: "select",
          label: "Gender",
          required: true,
          nemsisElement: "ePatient.13",
          options: [
            { label: "Male", value: "9906001" },
            { label: "Female", value: "9906003" },
            { label: "Unknown", value: "9906005" },
            { label: "Non-Binary", value: "9906007" },
          ],
          gridColumns: 1,
        },
        {
          id: "race",
          type: "select",
          label: "Race",
          nemsisElement: "ePatient.14",
          options: [
            { label: "American Indian or Alaska Native", value: "1002001" },
            { label: "Asian", value: "1002003" },
            { label: "Black or African American", value: "1002005" },
            { label: "Native Hawaiian or Pacific Islander", value: "1002007" },
            { label: "White", value: "1002009" },
            { label: "Unknown", value: "7701003" },
            { label: "Other", value: "7701005" },
          ],
          gridColumns: 1,
        },
        {
          id: "ethnicity",
          type: "select",
          label: "Ethnicity",
          nemsisElement: "ePatient.14",
          options: [
            { label: "Hispanic or Latino", value: "2514001" },
            { label: "Not Hispanic or Latino", value: "2514003" },
            { label: "Unknown", value: "7701003" },
          ],
          gridColumns: 1,
        },
        {
          id: "ssn",
          type: "ssn",
          label: "Social Security Number",
          nemsisElement: "ePatient.12",
          placeholder: "XXX-XX-XXXX",
          gridColumns: 1,
        },
        {
          id: "phone",
          type: "phone",
          label: "Phone Number",
          nemsisElement: "ePatient.18",
          placeholder: "(555) 123-4567",
          gridColumns: 1,
        },
        {
          id: "email",
          type: "text",
          label: "Email Address",
          nemsisElement: "ePatient.19",
          placeholder: "patient@example.com",
          gridColumns: 1,
        },
        {
          id: "address",
          type: "text",
          label: "Street Address",
          nemsisElement: "ePatient.10",
          placeholder: "123 Main St",
          gridColumns: 2,
        },
        {
          id: "city",
          type: "text",
          label: "City",
          nemsisElement: "ePatient.10",
          placeholder: "Milwaukee",
          gridColumns: 1,
        },
        {
          id: "state",
          type: "select",
          label: "State",
          nemsisElement: "ePatient.10",
          options: [
            { label: "Wisconsin", value: "WI" },
            { label: "Illinois", value: "IL" },
            { label: "Minnesota", value: "MN" },
            { label: "Iowa", value: "IA" },
            { label: "Michigan", value: "MI" },
          ],
          defaultValue: "WI",
          gridColumns: 1,
        },
        {
          id: "zip",
          type: "text",
          label: "ZIP Code",
          nemsisElement: "ePatient.10",
          placeholder: "53201",
          validation: { pattern: "^\\d{5}(-\\d{4})?$" },
          gridColumns: 1,
        },
        {
          id: "country",
          type: "select",
          label: "Country",
          nemsisElement: "ePatient.10",
          options: [
            { label: "United States", value: "US" },
            { label: "Canada", value: "CA" },
            { label: "Mexico", value: "MX" },
          ],
          defaultValue: "US",
          gridColumns: 1,
        },
      ],
    },
    {
      id: "chief_complaint",
      title: "Chief Complaint & History",
      nemsisSection: "eSituation",
      defaultExpanded: true,
      fields: [
        {
          id: "chief_complaint",
          type: "text",
          label: "Chief Complaint",
          required: true,
          nemsisElement: "eSituation.04",
          placeholder: "Chest pain, difficulty breathing, fall",
          aiSuggestion: {
            protocol: ["ALS", "PALS", "BLS"],
            triggers: ["vitals", "age"],
          },
          gridColumns: 2,
        },
        {
          id: "chief_complaint_code",
          type: "select",
          label: "Chief Complaint Code",
          nemsisElement: "eSituation.09",
          options: [
            { label: "Abdominal Pain", value: "2009001" },
            { label: "Allergic Reaction", value: "2009003" },
            { label: "Altered Mental Status", value: "2009005" },
            { label: "Cardiac Arrest", value: "2009007" },
            { label: "Chest Pain", value: "2009009" },
            { label: "Diabetic", value: "2009011" },
            { label: "Difficulty Breathing", value: "2009013" },
            { label: "Fall", value: "2009015" },
            { label: "Hemorrhage", value: "2009017" },
            { label: "Overdose/Poisoning", value: "2009019" },
            { label: "Seizure", value: "2009021" },
            { label: "Stroke/CVA", value: "2009023" },
            { label: "Trauma", value: "2009025" },
            { label: "Unconscious", value: "2009027" },
          ],
          gridColumns: 2,
        },
        {
          id: "primary_symptom",
          type: "select",
          label: "Primary Symptom",
          nemsisElement: "eSituation.11",
          options: [
            { label: "Airway Compromise", value: "2211001" },
            { label: "Apnea", value: "2211003" },
            { label: "Bleeding", value: "2211005" },
            { label: "Chest Pain", value: "2211007" },
            { label: "Confusion", value: "2211009" },
            { label: "Cough", value: "2211011" },
            { label: "Dizziness", value: "2211013" },
            { label: "Fever", value: "2211015" },
            { label: "Headache", value: "2211017" },
            { label: "Nausea/Vomiting", value: "2211019" },
            { label: "Pain", value: "2211021" },
            { label: "Shortness of Breath", value: "2211023" },
            { label: "Weakness", value: "2211025" },
          ],
          gridColumns: 2,
        },
        {
          id: "onset_datetime",
          type: "datetime",
          label: "Symptom Onset Date/Time",
          nemsisElement: "eSituation.03",
          gridColumns: 1,
        },
        {
          id: "duration",
          type: "text",
          label: "Duration of Symptoms",
          nemsisElement: "eSituation.05",
          placeholder: "2 hours, 30 minutes, etc.",
          gridColumns: 1,
        },
        {
          id: "history_present_illness",
          type: "textarea",
          label: "History of Present Illness",
          nemsisElement: "eHistory.01",
          placeholder: "Patient states...",
          gridColumns: 2,
        },
        {
          id: "past_medical_history",
          type: "textarea",
          label: "Past Medical History",
          nemsisElement: "eHistory.02",
          placeholder: "Hypertension, Diabetes, COPD, etc.",
          gridColumns: 2,
        },
        {
          id: "current_medications",
          type: "textarea",
          label: "Current Medications",
          nemsisElement: "eHistory.03",
          placeholder: "Lisinopril 10mg daily, Metformin 500mg BID, etc.",
          gridColumns: 2,
        },
        {
          id: "allergies",
          type: "textarea",
          label: "Allergies",
          nemsisElement: "eHistory.05",
          placeholder: "Penicillin, Latex, NKDA, etc.",
          quickPicks: ["NKDA", "Penicillin", "Sulfa", "Latex", "Morphine"],
          gridColumns: 2,
        },
        {
          id: "last_oral_intake",
          type: "text",
          label: "Last Oral Intake",
          nemsisElement: "eHistory.07",
          placeholder: "2 hours ago - breakfast",
          gridColumns: 1,
        },
        {
          id: "events_prior",
          type: "textarea",
          label: "Events Prior to Incident",
          nemsisElement: "eHistory.08",
          placeholder: "Patient was walking when...",
          gridColumns: 2,
        },
      ],
    },
    {
      id: "vitals",
      title: "Vital Signs",
      nemsisSection: "eVitals",
      defaultExpanded: true,
      fields: [
        {
          id: "vitals_set",
          type: "vitals-row",
          label: "Vital Signs Timeline",
          nemsisElement: "eVitals",
          required: true,
          gridColumns: 2,
        },
      ],
    },
    {
      id: "physical_exam",
      title: "Physical Assessment",
      nemsisSection: "eExam",
      fields: [
        {
          id: "general_appearance",
          type: "select",
          label: "General Appearance",
          nemsisElement: "eExam.01",
          options: [
            { label: "Normal", value: "3001001" },
            { label: "Abnormal", value: "3001003" },
            { label: "Not Done", value: "7701001" },
          ],
          gridColumns: 1,
        },
        {
          id: "mental_status",
          type: "select",
          label: "Mental Status",
          nemsisElement: "eExam.11",
          options: [
            { label: "Alert", value: "3011001" },
            { label: "Verbal Response", value: "3011003" },
            { label: "Painful Response", value: "3011005" },
            { label: "Unresponsive", value: "3011007" },
          ],
          quickPicks: ["Alert", "Verbal Response", "Painful Response", "Unresponsive"],
          gridColumns: 1,
        },
        {
          id: "gcs_eye",
          type: "select",
          label: "GCS - Eye Opening",
          nemsisElement: "eVitals.19",
          options: [
            { label: "4 - Spontaneous", value: "4" },
            { label: "3 - To Voice", value: "3" },
            { label: "2 - To Pain", value: "2" },
            { label: "1 - None", value: "1" },
          ],
          gridColumns: 1,
        },
        {
          id: "gcs_verbal",
          type: "select",
          label: "GCS - Verbal Response",
          nemsisElement: "eVitals.20",
          options: [
            { label: "5 - Oriented", value: "5" },
            { label: "4 - Confused", value: "4" },
            { label: "3 - Inappropriate Words", value: "3" },
            { label: "2 - Incomprehensible Sounds", value: "2" },
            { label: "1 - None", value: "1" },
          ],
          gridColumns: 1,
        },
        {
          id: "gcs_motor",
          type: "select",
          label: "GCS - Motor Response",
          nemsisElement: "eVitals.21",
          options: [
            { label: "6 - Obeys Commands", value: "6" },
            { label: "5 - Localizes Pain", value: "5" },
            { label: "4 - Withdraws from Pain", value: "4" },
            { label: "3 - Flexion to Pain", value: "3" },
            { label: "2 - Extension to Pain", value: "2" },
            { label: "1 - None", value: "1" },
          ],
          gridColumns: 1,
        },
        {
          id: "gcs_total",
          type: "number",
          label: "GCS Total",
          nemsisElement: "eVitals.23",
          placeholder: "Auto-calculated (3-15)",
          validation: { min: 3, max: 15 },
          gridColumns: 1,
        },
        {
          id: "head_exam",
          type: "select",
          label: "Head",
          nemsisElement: "eExam.03",
          options: [
            { label: "Normal", value: "normal" },
            { label: "Abnormal", value: "abnormal" },
            { label: "Not Examined", value: "not_done" },
          ],
          gridColumns: 1,
        },
        {
          id: "neck_exam",
          type: "select",
          label: "Neck",
          nemsisElement: "eExam.05",
          options: [
            { label: "Normal", value: "normal" },
            { label: "Abnormal - JVD", value: "jvd" },
            { label: "Abnormal - Tracheal Deviation", value: "tracheal_deviation" },
            { label: "Not Examined", value: "not_done" },
          ],
          gridColumns: 1,
        },
        {
          id: "chest_exam",
          type: "select",
          label: "Chest/Lungs",
          nemsisElement: "eExam.07",
          options: [
            { label: "Normal", value: "normal" },
            { label: "Abnormal - Wheezes", value: "wheezes" },
            { label: "Abnormal - Rales", value: "rales" },
            { label: "Abnormal - Diminished", value: "diminished" },
            { label: "Not Examined", value: "not_done" },
          ],
          gridColumns: 1,
        },
        {
          id: "heart_exam",
          type: "select",
          label: "Heart",
          nemsisElement: "eExam.09",
          options: [
            { label: "Normal", value: "normal" },
            { label: "Abnormal - Irregular", value: "irregular" },
            { label: "Abnormal - Murmur", value: "murmur" },
            { label: "Not Examined", value: "not_done" },
          ],
          gridColumns: 1,
        },
        {
          id: "abdomen_exam",
          type: "select",
          label: "Abdomen",
          nemsisElement: "eExam.11",
          options: [
            { label: "Normal", value: "normal" },
            { label: "Abnormal - Tender", value: "tender" },
            { label: "Abnormal - Distended", value: "distended" },
            { label: "Abnormal - Rigid", value: "rigid" },
            { label: "Not Examined", value: "not_done" },
          ],
          gridColumns: 1,
        },
        {
          id: "extremities_exam",
          type: "select",
          label: "Extremities",
          nemsisElement: "eExam.15",
          options: [
            { label: "Normal", value: "normal" },
            { label: "Abnormal - Deformity", value: "deformity" },
            { label: "Abnormal - Swelling", value: "swelling" },
            { label: "Abnormal - Weakness", value: "weakness" },
            { label: "Not Examined", value: "not_done" },
          ],
          gridColumns: 1,
        },
        {
          id: "skin_exam",
          type: "select",
          label: "Skin",
          nemsisElement: "eExam.17",
          options: [
            { label: "Normal", value: "normal" },
            { label: "Pale", value: "pale" },
            { label: "Flushed", value: "flushed" },
            { label: "Cyanotic", value: "cyanotic" },
            { label: "Diaphoretic", value: "diaphoretic" },
            { label: "Not Examined", value: "not_done" },
          ],
          gridColumns: 1,
        },
        {
          id: "neurological_exam",
          type: "textarea",
          label: "Neurological Assessment",
          nemsisElement: "eExam.13",
          placeholder: "Pupils, motor function, sensation...",
          gridColumns: 2,
        },
      ],
    },
    {
      id: "procedures",
      title: "Procedures & Interventions",
      nemsisSection: "eProcedures",
      fields: [
        {
          id: "procedures",
          type: "procedure-row",
          label: "Procedures Performed",
          nemsisElement: "eProcedures",
          gridColumns: 2,
        },
      ],
    },
    {
      id: "medications",
      title: "Medications Administered",
      nemsisSection: "eMedications",
      fields: [
        {
          id: "medications_administered",
          type: "medication-row",
          label: "Medications",
          nemsisElement: "eMedications",
          gridColumns: 2,
        },
        {
          id: "medication_ocr",
          type: "ocr",
          label: "Scan Medication Label",
          gridColumns: 2,
        },
      ],
    },
    {
      id: "narrative",
      title: "Patient Care Narrative",
      nemsisSection: "eNarrative",
      fields: [
        {
          id: "narrative_voice",
          type: "voice",
          label: "Voice Narrative",
          nemsisElement: "eNarrative.01",
          gridColumns: 2,
        },
        {
          id: "narrative_text",
          type: "textarea",
          label: "Narrative",
          required: true,
          nemsisElement: "eNarrative.01",
          placeholder: "Detailed patient care narrative...",
          gridColumns: 2,
        },
      ],
    },
    {
      id: "disposition",
      title: "Transport & Disposition",
      nemsisSection: "eDisposition",
      defaultExpanded: true,
      fields: [
        {
          id: "transport_mode",
          type: "select",
          label: "Transport Mode",
          required: true,
          nemsisElement: "eDisposition.22",
          options: [
            { label: "Emergency (Lights and Sirens)", value: "4222001" },
            { label: "Non-Emergency", value: "4222003" },
            { label: "Interfacility", value: "4222005" },
            { label: "Air Medical", value: "4222007" },
          ],
          gridColumns: 1,
        },
        {
          id: "transport_reason",
          type: "select",
          label: "Reason for Transport",
          nemsisElement: "eDisposition.21",
          options: [
            { label: "Emergency", value: "4221001" },
            { label: "Medical Necessity", value: "4221003" },
            { label: "Patient Request", value: "4221005" },
            { label: "Law Enforcement", value: "4221007" },
          ],
          gridColumns: 1,
        },
        {
          id: "destination_type",
          type: "select",
          label: "Destination Type",
          required: true,
          nemsisElement: "eDisposition.23",
          options: [
            { label: "Hospital Emergency Department", value: "4223001" },
            { label: "Urgent Care Facility", value: "4223003" },
            { label: "Clinic", value: "4223005" },
            { label: "Specialty Center", value: "4223007" },
            { label: "Patient Residence", value: "4223009" },
            { label: "Other", value: "4223011" },
          ],
          gridColumns: 2,
        },
        {
          id: "destination_name",
          type: "text",
          label: "Destination Name",
          required: true,
          nemsisElement: "eDisposition.01",
          placeholder: "Froedtert Hospital",
          gridColumns: 1,
        },
        {
          id: "destination_address",
          type: "text",
          label: "Destination Address",
          nemsisElement: "eDisposition.02",
          placeholder: "9200 W Wisconsin Ave",
          gridColumns: 1,
        },
        {
          id: "patient_acuity",
          type: "select",
          label: "Patient Acuity",
          nemsisElement: "eDisposition.27",
          options: [
            { label: "Critical", value: "4227001" },
            { label: "Emergent", value: "4227003" },
            { label: "Lower Acuity", value: "4227005" },
            { label: "Non-Acute", value: "4227007" },
          ],
          gridColumns: 1,
        },
        {
          id: "hospital_capability",
          type: "select",
          label: "Hospital Capability",
          nemsisElement: "eDisposition.26",
          options: [
            { label: "Trauma Center", value: "trauma" },
            { label: "Stroke Center", value: "stroke" },
            { label: "STEMI Center", value: "stemi" },
            { label: "Pediatric Center", value: "pediatric" },
            { label: "Burn Center", value: "burn" },
            { label: "None", value: "none" },
          ],
          gridColumns: 1,
        },
        {
          id: "incident_disposition",
          type: "select",
          label: "Incident Disposition",
          required: true,
          nemsisElement: "eDisposition.28",
          options: [
            { label: "Treated, Transported by EMS", value: "4228001" },
            { label: "Treated, Transported by Private Vehicle", value: "4228003" },
            { label: "Treated, Refused Transport", value: "4228005" },
            { label: "Patient Dead at Scene", value: "4228007" },
            { label: "No Patient Found", value: "4228009" },
            { label: "No Treatment Required", value: "4228011" },
          ],
          gridColumns: 2,
        },
      ],
    },
    {
      id: "crew_signatures",
      title: "Crew & Signatures",
      nemsisSection: "eSignatures",
      defaultExpanded: false,
      fields: [
        {
          id: "primary_provider",
          type: "text",
          label: "Primary Provider",
          required: true,
          nemsisElement: "eSignatures.01",
          placeholder: "Provider Name",
          gridColumns: 1,
        },
        {
          id: "primary_provider_cert",
          type: "select",
          label: "Certification Level",
          nemsisElement: "eSignatures.02",
          options: [
            { label: "Paramedic", value: "paramedic" },
            { label: "AEMT", value: "aemt" },
            { label: "EMT", value: "emt" },
            { label: "EMR", value: "emr" },
          ],
          gridColumns: 1,
        },
        {
          id: "primary_provider_signature",
          type: "signature",
          label: "Primary Provider Signature",
          required: true,
          nemsisElement: "eSignatures.03",
          gridColumns: 2,
        },
        {
          id: "additional_crew",
          type: "textarea",
          label: "Additional Crew Members",
          nemsisElement: "eSignatures.04",
          placeholder: "Name, Certification (one per line)",
          gridColumns: 2,
        },
        {
          id: "patient_signature",
          type: "signature",
          label: "Patient/Guardian Signature",
          nemsisElement: "eSignatures.10",
          gridColumns: 2,
        },
        {
          id: "receiving_provider",
          type: "text",
          label: "Receiving Provider Name",
          nemsisElement: "eSignatures.11",
          placeholder: "Dr. Smith, RN Johnson",
          gridColumns: 1,
        },
        {
          id: "receiving_provider_signature",
          type: "signature",
          label: "Receiving Provider Signature",
          nemsisElement: "eSignatures.12",
          gridColumns: 2,
        },
      ],
    },
  ],
  shortcuts: [
    {
      label: "IV 18g + NS",
      action: "add_procedure",
      fields: {
        type: "IV Access",
        size: "18g",
        location: "Left AC",
        medication: "Saline 0.9% NS",
        rate: "TKO",
      },
    },
    {
      label: "O2 2L NC",
      action: "add_procedure",
      fields: {
        type: "Oxygen Administration",
        dose: "2L",
        method: "Nasal Cannula",
      },
    },
    {
      label: "12-Lead EKG",
      action: "add_procedure",
      fields: {
        type: "12-Lead ECG",
        findings: "Normal Sinus Rhythm",
      },
    },
    {
      label: "CPR",
      action: "add_procedure",
      fields: {
        type: "Cardiopulmonary Resuscitation",
        notes: "High-quality CPR",
      },
    },
    {
      label: "Aspirin 324mg",
      action: "add_medication",
      fields: {
        name: "Aspirin",
        dose: "324",
        units: "mg",
        route: "PO",
      },
    },
    {
      label: "Nitro 0.4mg SL",
      action: "add_medication",
      fields: {
        name: "Nitroglycerin",
        dose: "0.4",
        units: "mg",
        route: "Sublingual",
      },
    },
  ],
};

// Fire Schema - Extends EMS with Fire-Specific Fields
export const fireSchema: EpcrSchema = {
  variant: "FIRE",
  sections: [
    ...emsSchema.sections.slice(0, -1), // All EMS sections except signatures
    {
      id: "fire_specific",
      title: "Fire/Rescue Information",
      nemsisSection: "eSituation",
      fields: [
        {
          id: "incident_type",
          type: "select",
          label: "Fire Incident Type",
          options: [
            { label: "Structure Fire", value: "structure" },
            { label: "Vehicle Fire", value: "vehicle" },
            { label: "Wildland Fire", value: "wildland" },
            { label: "Technical Rescue", value: "technical_rescue" },
            { label: "Hazmat", value: "hazmat" },
            { label: "Fire Alarm", value: "fire_alarm" },
            { label: "EMS Only", value: "ems_only" },
          ],
          gridColumns: 1,
        },
        {
          id: "fire_suppression",
          type: "select",
          label: "Fire Suppression Required",
          options: [
            { label: "Yes", value: "yes" },
            { label: "No", value: "no" },
          ],
          gridColumns: 1,
        },
        {
          id: "exposure_risk",
          type: "textarea",
          label: "Exposure/Contamination Risk",
          placeholder: "Smoke inhalation, chemical exposure, etc.",
          gridColumns: 2,
        },
        {
          id: "decontamination_required",
          type: "select",
          label: "Decontamination Required",
          options: [
            { label: "Yes", value: "yes" },
            { label: "No", value: "no" },
          ],
          gridColumns: 1,
        },
        {
          id: "extrication_required",
          type: "select",
          label: "Extrication Required",
          options: [
            { label: "Yes", value: "yes" },
            { label: "No", value: "no" },
          ],
          gridColumns: 1,
        },
        {
          id: "fire_notes",
          type: "textarea",
          label: "Fire-Specific Notes",
          placeholder: "Additional fire/rescue information...",
          gridColumns: 2,
        },
      ],
    },
    ...emsSchema.sections.slice(-1), // Signatures section
  ],
  shortcuts: emsSchema.shortcuts,
};

// HEMS Schema - Extends EMS with Critical Care Fields
export const hemsSchema: EpcrSchema = {
  variant: "HEMS",
  sections: [
    ...emsSchema.sections.slice(0, -2), // All EMS sections except narrative and signatures
    {
      id: "critical_care",
      title: "Critical Care Interventions",
      nemsisSection: "eProcedures",
      fields: [
        {
          id: "ventilator_mode",
          type: "select",
          label: "Ventilator Mode",
          options: [
            { label: "Not Ventilated", value: "none" },
            { label: "AC (Assist Control)", value: "ac" },
            { label: "SIMV", value: "simv" },
            { label: "PSV (Pressure Support)", value: "psv" },
            { label: "CPAP", value: "cpap" },
            { label: "BiPAP", value: "bipap" },
          ],
          gridColumns: 1,
        },
        {
          id: "ventilator_rate",
          type: "number",
          label: "Ventilator Rate (breaths/min)",
          placeholder: "12-20",
          gridColumns: 1,
        },
        {
          id: "fio2",
          type: "number",
          label: "FiO2 (%)",
          placeholder: "21-100",
          validation: { min: 21, max: 100 },
          gridColumns: 1,
        },
        {
          id: "peep",
          type: "number",
          label: "PEEP (cmH2O)",
          placeholder: "5-15",
          gridColumns: 1,
        },
        {
          id: "tidal_volume",
          type: "number",
          label: "Tidal Volume (mL)",
          placeholder: "400-600",
          gridColumns: 1,
        },
        {
          id: "peak_pressure",
          type: "number",
          label: "Peak Inspiratory Pressure (cmH2O)",
          gridColumns: 1,
        },
        {
          id: "vasopressor_drips",
          type: "textarea",
          label: "Vasopressor/Inotrope Infusions",
          placeholder: "Levophed 8mcg/min, Epinephrine 2mcg/min, etc.",
          gridColumns: 2,
        },
        {
          id: "sedation_drips",
          type: "textarea",
          label: "Sedation/Analgesia Drips",
          placeholder: "Propofol 30mcg/kg/min, Fentanyl 50mcg/hr, etc.",
          gridColumns: 2,
        },
        {
          id: "ecmo_status",
          type: "select",
          label: "ECMO Status",
          options: [
            { label: "Not in use", value: "none" },
            { label: "V-A ECMO", value: "va" },
            { label: "V-V ECMO", value: "vv" },
          ],
          gridColumns: 1,
        },
        {
          id: "iabp_status",
          type: "select",
          label: "IABP (Intra-Aortic Balloon Pump)",
          options: [
            { label: "Not in use", value: "none" },
            { label: "Active", value: "active" },
          ],
          gridColumns: 1,
        },
        {
          id: "advanced_monitoring",
          type: "textarea",
          label: "Advanced Monitoring",
          placeholder: "Arterial line, CVP, ICP monitor, etc.",
          gridColumns: 2,
        },
        {
          id: "blood_products",
          type: "textarea",
          label: "Blood Products Administered",
          placeholder: "pRBC 2 units, FFP 2 units, etc.",
          gridColumns: 2,
        },
      ],
    },
    {
      id: "flight_operations",
      title: "Flight Operations",
      fields: [
        {
          id: "aircraft_tail_number",
          type: "text",
          label: "Aircraft Tail Number",
          placeholder: "N123AB",
          gridColumns: 1,
        },
        {
          id: "flight_crew",
          type: "textarea",
          label: "Flight Crew",
          placeholder: "Pilot, Flight Paramedic, Flight Nurse",
          gridColumns: 1,
        },
        {
          id: "takeoff_time",
          type: "datetime",
          label: "Takeoff Time",
          gridColumns: 1,
        },
        {
          id: "landing_time",
          type: "datetime",
          label: "Landing Time",
          gridColumns: 1,
        },
        {
          id: "flight_conditions",
          type: "select",
          label: "Flight Conditions",
          options: [
            { label: "VFR (Visual)", value: "vfr" },
            { label: "IFR (Instrument)", value: "ifr" },
          ],
          gridColumns: 1,
        },
        {
          id: "weather_conditions",
          type: "text",
          label: "Weather Conditions",
          placeholder: "Clear, winds 5kts",
          gridColumns: 1,
        },
      ],
    },
    ...emsSchema.sections.slice(-2), // Narrative and signatures sections
  ],
  shortcuts: [
    ...emsSchema.shortcuts,
    {
      label: "RSI Protocol",
      action: "add_procedure",
      fields: {
        type: "Rapid Sequence Intubation",
        premedication: "Fentanyl, Lidocaine",
        induction: "Etomidate or Ketamine",
        paralytic: "Rocuronium or Succinylcholine",
      },
    },
    {
      label: "Vent Settings",
      action: "quick_fill",
      fields: {
        ventilator_mode: "ac",
        ventilator_rate: "12",
        fio2: "100",
        peep: "5",
        tidal_volume: "500",
      },
    },
  ],
};
