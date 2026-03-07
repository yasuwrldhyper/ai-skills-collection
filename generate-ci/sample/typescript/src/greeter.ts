/**
 * Greeter module providing greeting functionality.
 */

/**
 * Generates a greeting message for the given name.
 * @param name - The name of the person to greet
 * @returns A greeting string
 */
export function greet(name: string): string {
  if (!name || name.trim().length === 0) {
    return 'Hello, World!';
  }
  return `Hello, ${name.trim()}!`;
}
