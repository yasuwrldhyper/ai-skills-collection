import { describe, it, expect } from 'vitest'
import { greet } from '../src/greeter'

describe('greet', () => {
  it('returns a greeting with the given name', () => {
    expect(greet('Alice')).toBe('Hello, Alice!')
  })

  it('trims whitespace from the name', () => {
    expect(greet('  Bob  ')).toBe('Hello, Bob!')
  })

  it('returns a default greeting when name is empty', () => {
    expect(greet('')).toBe('Hello, World!')
  })

  it('returns a default greeting when name is only whitespace', () => {
    expect(greet('   ')).toBe('Hello, World!')
  })
})
