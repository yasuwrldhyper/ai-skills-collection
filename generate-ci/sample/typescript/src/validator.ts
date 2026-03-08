/**
 * String validator module providing common validation functions.
 */

/**
 * Validates whether a string is a valid email address.
 * @param value - The string to validate
 * @returns True if the string is a valid email address, false otherwise
 */
export function isEmail(value: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(value);
}

/**
 * Validates whether a string is a valid URL.
 * @param value - The string to validate
 * @returns True if the string is a valid URL, false otherwise
 */
export function isUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}

/**
 * Checks whether a string is empty or contains only whitespace.
 * @param value - The string to check
 * @returns True if the string is empty or whitespace-only, false otherwise
 */
export function isEmpty(value: string): boolean {
  return value.trim().length === 0;
}
