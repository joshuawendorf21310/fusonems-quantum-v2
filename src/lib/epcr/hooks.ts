import { useState, useEffect, useCallback, useRef } from "react";
import { EpcrRecord, ValidationError } from "./types";
import {
  validateEmail,
  validatePhone,
  validateDate,
  validateDateNotFuture,
  validateRequired,
} from "../utils/validation";

const AUTO_SAVE_INTERVAL = 30000; // 30 seconds

export const useEpcrForm = (initialData?: Partial<EpcrRecord> & { variant?: string }) => {
  const [formData, setFormData] = useState<Partial<EpcrRecord>>(initialData || {});
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Save to localStorage function (must be defined before useEffect)
  const saveToLocalStorage = useCallback(() => {
    try {
      localStorage.setItem("epcr_draft", JSON.stringify(formData));
      setLastSaved(new Date());
      console.log("Auto-saved to local storage");
    } catch (err) {
      console.error("Failed to save to localStorage:", err);
    }
  }, [formData]);

  // Auto-save effect
  useEffect(() => {
    if (isDirty) {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
      autoSaveTimerRef.current = setTimeout(() => {
        saveToLocalStorage();
      }, AUTO_SAVE_INTERVAL);
    }
    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [isDirty, saveToLocalStorage]);

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("epcr_draft");
    if (saved && !initialData?.id) {
      try {
        const parsed = JSON.parse(saved);
        setFormData(parsed);
      } catch (err) {
        console.error("Failed to parse saved draft:", err);
      }
    }
  }, []);

  const updateField = useCallback((field: string, value: unknown) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setIsDirty(true);
  }, []);

  const validateForm = useCallback(() => {
    const newErrors: ValidationError[] = [];
    
    // Required fields
    const firstName = formData.patient?.first_name || formData.first_name;
    const lastName = formData.patient?.last_name || formData.last_name;
    
    const firstNameValidation = validateRequired(firstName);
    if (!firstNameValidation.isValid) {
      newErrors.push({ field: "first_name", message: "First name required", severity: "ERROR" });
    }
    
    const lastNameValidation = validateRequired(lastName);
    if (!lastNameValidation.isValid) {
      newErrors.push({ field: "last_name", message: "Last name required", severity: "ERROR" });
    }
    
    const chiefComplaintValidation = validateRequired(formData.chief_complaint);
    if (!chiefComplaintValidation.isValid) {
      newErrors.push({ field: "chief_complaint", message: "Chief complaint required", severity: "ERROR" });
    }

    // Email validation
    if (formData.patient?.email || formData.email) {
      const email = formData.patient?.email || formData.email;
      const emailValidation = validateEmail(email as string);
      if (!emailValidation.isValid) {
        newErrors.push({ field: "email", message: emailValidation.error || "Invalid email", severity: "ERROR" });
      }
    }

    // Phone validation
    if (formData.patient?.phone || formData.phone) {
      const phone = formData.patient?.phone || formData.phone;
      const phoneValidation = validatePhone(phone as string);
      if (!phoneValidation.isValid) {
        newErrors.push({ field: "phone", message: phoneValidation.error || "Invalid phone number", severity: "ERROR" });
      }
    }

    // Date of birth validation
    if (formData.patient?.date_of_birth || formData.date_of_birth) {
      const dob = formData.patient?.date_of_birth || formData.date_of_birth;
      const dobValidation = validateDateNotFuture(dob as string);
      if (!dobValidation.isValid) {
        newErrors.push({ field: "date_of_birth", message: dobValidation.error || "Invalid date of birth", severity: "ERROR" });
      }
    }

    // Incident date validation
    if (formData.incident_date) {
      const incidentDateValidation = validateDateNotFuture(formData.incident_date as string);
      if (!incidentDateValidation.isValid) {
        newErrors.push({ field: "incident_date", message: incidentDateValidation.error || "Invalid incident date", severity: "ERROR" });
      }
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  }, [formData]);

  const saveForm = useCallback(async () => {
    if (!validateForm()) return false;
    
    setIsSaving(true);
    try {
      // Try online save first
      if (navigator.onLine) {
        const response = await fetch("/api/epcr/records", {
          method: formData.id ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formData),
        });
        
        if (!response.ok) throw new Error("Failed to save");
        
        const saved = await response.json();
        setFormData(saved);
        setIsDirty(false);
        localStorage.removeItem("epcr_draft");
        setLastSaved(new Date());
        return true;
      } else {
        // Offline: save to IndexedDB
        await saveToIndexedDB(formData);
        setIsDirty(false);
        setLastSaved(new Date());
        return true;
      }
    } catch (err) {
      console.error("Save error:", err);
      // Fallback to IndexedDB if online save fails
      await saveToIndexedDB(formData);
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [formData, validateForm]);

  return {
    formData,
    updateField,
    errors,
    isDirty,
    isSaving,
    validateForm,
    saveForm,
    lastSaved,
  };
};

export const useOfflineSync = () => {
  const [isOnline, setIsOnline] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);

  const checkPendingRecords = useCallback(async () => {
    try {
      const db = await openIndexedDB();
      const tx = db.transaction("epcr_offline", "readonly");
      const store = tx.objectStore("epcr_offline");
      const count = await store.count();
      setPendingCount(count);
    } catch (err) {
      console.error("Failed to check pending records:", err);
    }
  }, []);

  const syncPendingRecords = useCallback(async () => {
    try {
      const db = await openIndexedDB();
      const tx = db.transaction("epcr_offline", "readwrite");
      const store = tx.objectStore("epcr_offline");
      const records = await store.getAll();

      for (const record of records) {
        try {
          const response = await fetch("/api/epcr/records", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(record.data),
          });

          if (response.ok) {
            await store.delete(record.id);
            console.log(`Synced record ${record.id}`);
          }
        } catch (err) {
          console.error(`Failed to sync record ${record.id}:`, err);
        }
      }

      await checkPendingRecords();
    } catch (err) {
      console.error("Failed to sync pending records:", err);
    }
  }, [checkPendingRecords]);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      syncPendingRecords();
    };
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    setIsOnline(navigator.onLine);
    
    // Check for pending records on mount
    checkPendingRecords();

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [checkPendingRecords, syncPendingRecords]);

  return { isOnline, pendingCount, syncPendingRecords };
};

// IndexedDB utilities
async function openIndexedDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("FusionEMS_ePCR", 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains("epcr_offline")) {
        db.createObjectStore("epcr_offline", { keyPath: "id", autoIncrement: true });
      }
    };
  });
}

async function saveToIndexedDB(data: any): Promise<void> {
  const db = await openIndexedDB();
  const tx = db.transaction("epcr_offline", "readwrite");
  const store = tx.objectStore("epcr_offline");
  
  await store.add({
    data,
    timestamp: new Date().toISOString(),
  });
  
  console.log("Saved to IndexedDB for offline sync");
}
