/**
 * Validation utility functions for common input patterns
 */

export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

/**
 * Validates an email address
 */
export function validateEmail(email: string): ValidationResult {
  if (!email || email.trim() === '') {
    return { isValid: false, error: 'Email is required' };
  }

  // RFC 5322 compliant email regex (simplified)
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
  if (!emailRegex.test(email)) {
    return { isValid: false, error: 'Invalid email format' };
  }

  // Additional checks
  if (email.length > 254) {
    return { isValid: false, error: 'Email is too long (max 254 characters)' };
  }

  return { isValid: true };
}

/**
 * Validates a phone number (US format)
 * Accepts formats: (555) 123-4567, 555-123-4567, 5551234567, etc.
 */
export function validatePhone(phone: string): ValidationResult {
  if (!phone || phone.trim() === '') {
    return { isValid: false, error: 'Phone number is required' };
  }

  // Remove all non-digit characters for validation
  const digitsOnly = phone.replace(/\D/g, '');
  
  if (digitsOnly.length < 10) {
    return { isValid: false, error: 'Phone number must contain at least 10 digits' };
  }

  if (digitsOnly.length > 11) {
    return { isValid: false, error: 'Phone number is too long' };
  }

  // If 11 digits, first should be 1 (US country code)
  if (digitsOnly.length === 11 && digitsOnly[0] !== '1') {
    return { isValid: false, error: 'Invalid country code' };
  }

  return { isValid: true };
}

/**
 * Validates a date string
 */
export function validateDate(date: string): ValidationResult {
  if (!date || date.trim() === '') {
    return { isValid: false, error: 'Date is required' };
  }

  const dateObj = new Date(date);
  
  if (isNaN(dateObj.getTime())) {
    return { isValid: false, error: 'Invalid date format' };
  }

  return { isValid: true };
}

/**
 * Validates a date is not in the future
 */
export function validateDateNotFuture(date: string): ValidationResult {
  const baseValidation = validateDate(date);
  if (!baseValidation.isValid) {
    return baseValidation;
  }

  const dateObj = new Date(date);
  const now = new Date();
  
  if (dateObj > now) {
    return { isValid: false, error: 'Date cannot be in the future' };
  }

  return { isValid: true };
}

/**
 * Validates a date is not in the past
 */
export function validateDateNotPast(date: string): ValidationResult {
  const baseValidation = validateDate(date);
  if (!baseValidation.isValid) {
    return baseValidation;
  }

  const dateObj = new Date(date);
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  
  if (dateObj < now) {
    return { isValid: false, error: 'Date cannot be in the past' };
  }

  return { isValid: true };
}

/**
 * Validates a date range (start date must be before end date)
 */
export function validateDateRange(startDate: string, endDate: string): ValidationResult {
  const startValidation = validateDate(startDate);
  if (!startValidation.isValid) {
    return { isValid: false, error: `Start date: ${startValidation.error}` };
  }

  const endValidation = validateDate(endDate);
  if (!endValidation.isValid) {
    return { isValid: false, error: `End date: ${endValidation.error}` };
  }

  const start = new Date(startDate);
  const end = new Date(endDate);
  
  if (start > end) {
    return { isValid: false, error: 'Start date must be before end date' };
  }

  return { isValid: true };
}

/**
 * Validates a datetime string
 */
export function validateDateTime(datetime: string): ValidationResult {
  if (!datetime || datetime.trim() === '') {
    return { isValid: false, error: 'Date and time is required' };
  }

  const dateObj = new Date(datetime);
  
  if (isNaN(dateObj.getTime())) {
    return { isValid: false, error: 'Invalid date/time format' };
  }

  return { isValid: true };
}

/**
 * Validates a time string (HH:MM format)
 */
export function validateTime(time: string): ValidationResult {
  if (!time || time.trim() === '') {
    return { isValid: false, error: 'Time is required' };
  }

  const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;
  
  if (!timeRegex.test(time)) {
    return { isValid: false, error: 'Invalid time format (expected HH:MM)' };
  }

  return { isValid: true };
}

/**
 * Validates a required field
 */
export function validateRequired(value: any): ValidationResult {
  if (value === null || value === undefined || value === '') {
    return { isValid: false, error: 'This field is required' };
  }

  if (typeof value === 'string' && value.trim() === '') {
    return { isValid: false, error: 'This field is required' };
  }

  if (Array.isArray(value) && value.length === 0) {
    return { isValid: false, error: 'At least one item is required' };
  }

  return { isValid: true };
}

/**
 * Validates a number is within a range
 */
export function validateNumberRange(
  value: number,
  min?: number,
  max?: number
): ValidationResult {
  if (value === null || value === undefined || isNaN(value)) {
    return { isValid: false, error: 'Invalid number' };
  }

  if (min !== undefined && value < min) {
    return { isValid: false, error: `Value must be at least ${min}` };
  }

  if (max !== undefined && value > max) {
    return { isValid: false, error: `Value must be at most ${max}` };
  }

  return { isValid: true };
}

/**
 * Validates a string length
 */
export function validateStringLength(
  value: string,
  min?: number,
  max?: number
): ValidationResult {
  if (!value) {
    return { isValid: false, error: 'This field is required' };
  }

  const length = value.trim().length;

  if (min !== undefined && length < min) {
    return { isValid: false, error: `Must be at least ${min} characters` };
  }

  if (max !== undefined && length > max) {
    return { isValid: false, error: `Must be at most ${max} characters` };
  }

  return { isValid: true };
}

/**
 * Validates a SSN format (XXX-XX-XXXX)
 */
export function validateSSN(ssn: string): ValidationResult {
  if (!ssn || ssn.trim() === '') {
    return { isValid: false, error: 'SSN is required' };
  }

  const ssnRegex = /^\d{3}-\d{2}-\d{4}$/;
  const digitsOnly = ssn.replace(/\D/g, '');

  if (digitsOnly.length !== 9) {
    return { isValid: false, error: 'SSN must contain 9 digits' };
  }

  // Check for invalid SSNs (all zeros, all same digit, etc.)
  if (digitsOnly === '000000000' || /^(\d)\1{8}$/.test(digitsOnly)) {
    return { isValid: false, error: 'Invalid SSN' };
  }

  return { isValid: true };
}

/**
 * Validates a ZIP code (US format)
 */
export function validateZipCode(zip: string): ValidationResult {
  if (!zip || zip.trim() === '') {
    return { isValid: false, error: 'ZIP code is required' };
  }

  const zipRegex = /^\d{5}(-\d{4})?$/;
  
  if (!zipRegex.test(zip)) {
    return { isValid: false, error: 'Invalid ZIP code format (expected 12345 or 12345-6789)' };
  }

  return { isValid: true };
}
