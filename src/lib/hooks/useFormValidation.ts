import { useState, useCallback, useMemo } from "react";
import {
  validateEmail,
  validatePhone,
  validateDate,
  validateDateNotFuture,
  validateDateNotPast,
  validateDateRange,
  validateDateTime,
  validateTime,
  validateRequired,
  validateNumberRange,
  validateStringLength,
  validateSSN,
  validateZipCode,
  ValidationResult,
} from "../utils/validation";

export type ValidationRule =
  | { type: "required" }
  | { type: "email" }
  | { type: "phone" }
  | { type: "date" }
  | { type: "dateNotFuture" }
  | { type: "dateNotPast" }
  | { type: "datetime" }
  | { type: "time" }
  | { type: "ssn" }
  | { type: "zipCode" }
  | { type: "numberRange"; min?: number; max?: number }
  | { type: "stringLength"; min?: number; max?: number }
  | { type: "custom"; validator: (value: any) => ValidationResult };

export interface FieldValidation {
  rules: ValidationRule[];
  errorMessage?: string;
}

export interface FormValidationSchema {
  [fieldName: string]: FieldValidation;
}

export interface ValidationErrors {
  [fieldName: string]: string | undefined;
}

export interface UseFormValidationOptions<T> {
  schema: FormValidationSchema;
  initialValues?: Partial<T>;
  onSubmit?: (values: T) => void | Promise<void>;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
}

export interface UseFormValidationReturn<T> {
  values: Partial<T>;
  errors: ValidationErrors;
  touched: { [fieldName: string]: boolean };
  isValid: boolean;
  isSubmitting: boolean;
  setValue: (field: keyof T, value: any) => void;
  setValues: (values: Partial<T>) => void;
  setError: (field: keyof T, error: string | undefined) => void;
  setTouched: (field: keyof T, touched?: boolean) => void;
  validateField: (field: keyof T) => boolean;
  validateForm: () => boolean;
  handleChange: (field: keyof T) => (value: any) => void;
  handleBlur: (field: keyof T) => () => void;
  handleSubmit: (e?: React.FormEvent) => Promise<void>;
  reset: () => void;
  resetErrors: () => void;
}

/**
 * Reusable form validation hook
 */
export function useFormValidation<T extends Record<string, any>>(
  options: UseFormValidationOptions<T>
): UseFormValidationReturn<T> {
  const {
    schema,
    initialValues = {},
    onSubmit,
    validateOnChange = false,
    validateOnBlur = true,
  } = options;

  const [values, setValuesState] = useState<Partial<T>>(initialValues);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [touched, setTouched] = useState<{ [fieldName: string]: boolean }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Validate a single field
  const validateField = useCallback(
    (field: keyof T): boolean => {
      const fieldName = String(field);
      const fieldSchema = schema[fieldName];

      if (!fieldSchema) {
        return true; // No validation rules, consider valid
      }

      const value = values[field];
      let fieldError: string | undefined;

      for (const rule of fieldSchema.rules) {
        let result: ValidationResult;

        switch (rule.type) {
          case "required":
            result = validateRequired(value);
            break;
          case "email":
            result = validateEmail(value as string);
            break;
          case "phone":
            result = validatePhone(value as string);
            break;
          case "date":
            result = validateDate(value as string);
            break;
          case "dateNotFuture":
            result = validateDateNotFuture(value as string);
            break;
          case "dateNotPast":
            result = validateDateNotPast(value as string);
            break;
          case "datetime":
            result = validateDateTime(value as string);
            break;
          case "time":
            result = validateTime(value as string);
            break;
          case "ssn":
            result = validateSSN(value as string);
            break;
          case "zipCode":
            result = validateZipCode(value as string);
            break;
          case "numberRange":
            result = validateNumberRange(value as number, rule.min, rule.max);
            break;
          case "stringLength":
            result = validateStringLength(value as string, rule.min, rule.max);
            break;
          case "custom":
            result = rule.validator(value);
            break;
          default:
            result = { isValid: true };
        }

        if (!result.isValid) {
          fieldError = result.error || fieldSchema.errorMessage || "Invalid value";
          break;
        }
      }

      setErrors((prev) => ({
        ...prev,
        [fieldName]: fieldError,
      }));

      return !fieldError;
    },
    [schema, values]
  );

  // Validate all fields
  const validateForm = useCallback((): boolean => {
    let isValid = true;
    const newErrors: ValidationErrors = {};

    for (const fieldName in schema) {
      const fieldSchema = schema[fieldName];
      const value = values[fieldName as keyof T];

      for (const rule of fieldSchema.rules) {
        let result: ValidationResult;

        switch (rule.type) {
          case "required":
            result = validateRequired(value);
            break;
          case "email":
            result = validateEmail(value as string);
            break;
          case "phone":
            result = validatePhone(value as string);
            break;
          case "date":
            result = validateDate(value as string);
            break;
          case "dateNotFuture":
            result = validateDateNotFuture(value as string);
            break;
          case "dateNotPast":
            result = validateDateNotPast(value as string);
            break;
          case "datetime":
            result = validateDateTime(value as string);
            break;
          case "time":
            result = validateTime(value as string);
            break;
          case "ssn":
            result = validateSSN(value as string);
            break;
          case "zipCode":
            result = validateZipCode(value as string);
            break;
          case "numberRange":
            result = validateNumberRange(value as number, rule.min, rule.max);
            break;
          case "stringLength":
            result = validateStringLength(value as string, rule.min, rule.max);
            break;
          case "custom":
            result = rule.validator(value);
            break;
          default:
            result = { isValid: true };
        }

        if (!result.isValid) {
          newErrors[fieldName] =
            result.error || fieldSchema.errorMessage || "Invalid value";
          isValid = false;
          break;
        }
      }
    }

    setErrors(newErrors);
    return isValid;
  }, [schema, values]);

  // Set a single value
  const setValue = useCallback((field: keyof T, value: any) => {
    setValuesState((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear error when value changes
    if (errors[String(field)]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[String(field)];
        return newErrors;
      });
    }

    // Validate on change if enabled
    if (validateOnChange) {
      setTimeout(() => validateField(field), 0);
    }
  }, [errors, validateOnChange, validateField]);

  // Set multiple values
  const setValues = useCallback((newValues: Partial<T>) => {
    setValuesState((prev) => ({
      ...prev,
      ...newValues,
    }));
  }, []);

  // Set error manually
  const setError = useCallback((field: keyof T, error: string | undefined) => {
    setErrors((prev) => ({
      ...prev,
      [String(field)]: error,
    }));
  }, []);

  // Set touched state
  const setTouchedState = useCallback((field: keyof T, touchedValue: boolean = true) => {
    setTouched((prev) => ({
      ...prev,
      [String(field)]: touchedValue,
    }));
  }, []);

  // Handle field change
  const handleChange = useCallback(
    (field: keyof T) => (value: any) => {
      setValue(field, value);
    },
    [setValue]
  );

  // Handle field blur
  const handleBlur = useCallback(
    (field: keyof T) => () => {
      setTouchedState(field, true);
      if (validateOnBlur) {
        validateField(field);
      }
    },
    [setTouchedState, validateOnBlur, validateField]
  );

  // Handle form submit
  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();

      if (!validateForm()) {
        // Mark all fields as touched
        const allTouched: { [fieldName: string]: boolean } = {};
        for (const fieldName in schema) {
          allTouched[fieldName] = true;
        }
        setTouched(allTouched);
        return;
      }

      if (onSubmit) {
        setIsSubmitting(true);
        try {
          await onSubmit(values as T);
        } catch (error) {
          console.error("Form submission error:", error);
        } finally {
          setIsSubmitting(false);
        }
      }
    },
    [validateForm, onSubmit, values, schema]
  );

  // Reset form
  const reset = useCallback(() => {
    setValuesState(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  // Reset errors only
  const resetErrors = useCallback(() => {
    setErrors({});
  }, []);

  // Check if form is valid
  const isValid = useMemo(() => {
    return Object.keys(errors).length === 0;
  }, [errors]);

  return {
    values,
    errors,
    touched,
    isValid,
    isSubmitting,
    setValue,
    setValues,
    setError,
    setTouched: setTouchedState,
    validateField,
    validateForm,
    handleChange,
    handleBlur,
    handleSubmit,
    reset,
    resetErrors,
  };
}
