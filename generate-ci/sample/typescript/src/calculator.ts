/**
 * Calculator module providing basic arithmetic operations.
 */

/**
 * Adds two numbers together.
 * @param a - The first operand
 * @param b - The second operand
 * @returns The sum of a and b
 */
export function add(a: number, b: number): number {
  return a + b;
}

/**
 * Subtracts the second number from the first.
 * @param a - The minuend
 * @param b - The subtrahend
 * @returns The difference of a and b
 */
export function subtract(a: number, b: number): number {
  return a - b;
}

/**
 * Multiplies two numbers together.
 * @param a - The first factor
 * @param b - The second factor
 * @returns The product of a and b
 */
export function multiply(a: number, b: number): number {
  return a * b;
}

/**
 * Divides the first number by the second.
 * @param a - The dividend
 * @param b - The divisor (must not be zero)
 * @returns The quotient of a divided by b
 * @throws {Error} When dividing by zero
 */
export function divide(a: number, b: number): number {
  if (b === 0) {
    throw new Error('Division by zero is not allowed');
  }
  return a / b;
}
