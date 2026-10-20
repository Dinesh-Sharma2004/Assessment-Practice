import { describe, expect, it } from 'vitest'
import { fmtNum, niceMax, pieAngles, ticks } from './chartMath'

describe('chart helpers', () => {
  it('rounds axis maxima up to nice numbers', () => {
    expect(niceMax(87)).toBe(100); expect(niceMax(130)).toBe(200); expect(niceMax(4.2)).toBe(5); expect(niceMax(0)).toBe(1); expect(niceMax(2300)).toBe(2500)
  })
  it('builds evenly spaced ticks', () => {
    expect(ticks(87)).toEqual([0, 20, 40, 60, 80, 100])
  })
  it('formats numbers compactly', () => {
    expect(fmtNum(3)).toBe('3'); expect(fmtNum(2.5)).toBe('2.5'); expect(fmtNum(12.3456)).toBe('12.35')
  })
  it('pie slices cover the full circle', () => {
    const a = pieAngles([25, 25, 50])
    expect(a[0].start).toBeCloseTo(-Math.PI / 2); expect(a[2].end - a[0].start).toBeCloseTo(Math.PI * 2)
  })
})
