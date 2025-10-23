/**
 * Utility functions for handling API errors consistently across the application.
 * 
 * Pydantic validation errors come back as arrays of objects with structure:
 * { type, loc, msg, input, ctx, url }
 * 
 * This module provides functions to extract user-friendly error messages from various error formats.
 */

/**
 * Extract a user-friendly error message from an API error response.
 * 
 * Handles multiple error formats:
 * - String errors (FastAPI HTTPException detail)
 * - Pydantic validation errors (array of error objects)
 * - Generic error objects
 * 
 * @param err - The error object from an API call
 * @returns A user-friendly error message string
 */
export function extractErrorMessage(err: any): string {
  const detail = err?.response?.data?.detail;
  
  // If detail is a string, return it
  if (typeof detail === 'string') {
    return detail;
  }
  
  // If detail is an array (Pydantic validation errors)
  if (Array.isArray(detail)) {
    return detail.map((e: any) => {
      // Extract field path from loc array (e.g., ['body', 'name'] -> 'body.name')
      const field = Array.isArray(e.loc) && e.loc.length > 0 
        ? e.loc.slice(1).join('.') || e.loc.join('.') // Skip first element if it's 'body'
        : 'field';
      
      const message = e.msg || 'validation error';
      
      // Make the field name more user-friendly
      const friendlyField = field
        .replace(/_/g, ' ')
        .replace(/\./g, ' → ')
        .split(' ')
        .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      
      return `${friendlyField}: ${message}`;
    }).join('; ');
  }
  
  // If detail is an object with msg property (single validation error)
  if (detail && typeof detail === 'object' && detail.msg) {
    const field = detail.loc?.join('.') || '';
    return field ? `${field}: ${detail.msg}` : detail.msg;
  }
  
  // Check for error message in other common locations
  if (err?.response?.data?.message) {
    return err.response.data.message;
  }
  
  if (err?.message) {
    return err.message;
  }
  
  // Fallback to generic error message
  return 'An unexpected error occurred';
}

/**
 * Format a validation error for display in a form field.
 * Extracts only the message part without the field name.
 * 
 * @param err - The error object from an API call
 * @param fieldName - The field name to extract error for
 * @returns The error message for that field, or null if no error
 */
export function getFieldError(err: any, fieldName: string): string | null {
  const detail = err?.response?.data?.detail;
  
  if (!Array.isArray(detail)) {
    return null;
  }
  
  const fieldError = detail.find((e: any) => {
    if (!Array.isArray(e.loc)) return false;
    // Check if this error is for our field (loc is like ['body', 'field_name'])
    return e.loc.includes(fieldName) || e.loc[e.loc.length - 1] === fieldName;
  });
  
  return fieldError ? fieldError.msg : null;
}

/**
 * Check if an error is a validation error (422 status code).
 * 
 * @param err - The error object from an API call
 * @returns True if this is a validation error
 */
export function isValidationError(err: any): boolean {
  return err?.response?.status === 422;
}

/**
 * Check if an error is a not found error (404 status code).
 * 
 * @param err - The error object from an API call
 * @returns True if this is a not found error
 */
export function isNotFoundError(err: any): boolean {
  return err?.response?.status === 404;
}

/**
 * Check if an error is an authentication error (401 status code).
 * 
 * @param err - The error object from an API call
 * @returns True if this is an authentication error
 */
export function isAuthError(err: any): boolean {
  return err?.response?.status === 401;
}
