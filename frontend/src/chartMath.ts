/** Pure helpers for the SVG charts (unit-tested). */
export function niceMax(max: number): number {
  if (max <= 0) return 1
  const pow = Math.pow(10, Math.floor(Math.log10(max)))
  const f = max / pow
  const nice = f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10
  return nice * pow
}

export function ticks(max: number, count = 5): number[] {
  const top = niceMax(max)
  return Array.from({ length: count + 1 }, (_, i) => (top * i) / count)
}

export function fmtNum(v: number): string {
  return Math.abs(v - Math.round(v)) < 1e-9 ? String(Math.round(v)) : v.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
}

/** Angles (radians) for pie slices; the first slice starts at 12 o'clock. */
export function pieAngles(values: number[]): { start: number; end: number }[] {
  const total = values.reduce((a, b) => a + b, 0) || 1
  let a = -Math.PI / 2
  return values.map((v) => {
    const start = a, end = a + (v / total) * Math.PI * 2
    a = end
    return { start, end }
  })
}
