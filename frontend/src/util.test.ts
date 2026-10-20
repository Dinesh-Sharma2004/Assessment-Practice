import { describe, expect, it } from 'vitest'
import { counts, fmtClock, isAnswered, paletteState, remainingFrom } from './util'

const mcq = { id: 'a', type: 'mcq', marks: 40, statement: '' } as never
const sql = { id: 'b', type: 'sql', marks: 100, statement: '', starterQuery: 'SELECT 1;' } as never

describe('timer helpers', () => {
  it('formats clocks', () => {
    expect(fmtClock(4200)).toBe('1:10:00'); expect(fmtClock(61)).toBe('01:01'); expect(fmtClock(-5)).toBe('00:00'); expect(fmtClock(0.2)).toBe('00:01')
  })
  it('counts down from the server snapshot and never goes negative', () => {
    expect(remainingFrom(100, 1000, 31000)).toBe(70); expect(remainingFrom(10, 0, 99999)).toBe(0)
  })
})

describe('palette states', () => {
  it('classifies questions', () => {
    expect(paletteState(mcq, undefined, 0)).toBe('unvisited')
    expect(paletteState(mcq, { value: null, review: false, visited: true }, 0)).toBe('visited')
    expect(paletteState(mcq, { value: 'A', review: false, visited: true }, 0)).toBe('answered')
    expect(paletteState(mcq, { value: 'A', review: true, visited: true }, 0)).toBe('review')
  })
  it('does not count untouched starter code as answered', () => {
    expect(isAnswered(sql, { value: 'SELECT 1;', review: false, visited: true }, 0)).toBe(false)
    expect(isAnswered(sql, { value: 'SELECT 2;', review: false, visited: true }, 0)).toBe(true)
    expect(isAnswered(sql, { value: 'SELECT 1;', review: false, visited: true }, 1)).toBe(true)
  })
  it('summarises counts', () => {
    const c = counts([mcq, sql], { a: { value: 'B', review: true, visited: true } })
    expect(c).toEqual({ answered: 1, unanswered: 1, review: 1 })
  })
})
