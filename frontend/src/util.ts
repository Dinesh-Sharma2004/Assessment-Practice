import type { Answer, Q } from './types'

export const SECTION_LABEL: Record<string, string> = { mcq: 'CS/AI/ML/Stats', apt: 'Aptitude', da: 'Data Analysis', sql: 'SQL', pandas: 'Pandas', dsa: 'DSA' }

export function fmtClock(sec: number): string {
  const s = Math.max(0, Math.ceil(sec))
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60
  const mm = String(m).padStart(2, '0'), ss = String(r).padStart(2, '0')
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`
}

/** Remaining seconds computed from the moment a server snapshot was received (immune to local clock changes). */
export function remainingFrom(snapshotRemaining: number, receivedAtPerf: number, nowPerf: number): number {
  return Math.max(0, snapshotRemaining - (nowPerf - receivedAtPerf) / 1000)
}

export function starterOf(q: Q): string {
  return (q.starterQuery ?? q.starterCode ?? '') as string
}

export function isAnswered(q: Q, a: Answer | undefined, submitted: number): boolean {
  if (!a || a.value == null || a.value === '') return submitted > 0
  if (q.type === 'mcq') return true
  return submitted > 0 || a.value.trim() !== starterOf(q).trim()
}

export type PaletteState = 'answered' | 'review' | 'visited' | 'unvisited'
export function paletteState(q: Q, a: Answer | undefined, submitted: number): PaletteState {
  if (a?.review) return 'review'
  if (isAnswered(q, a, submitted)) return 'answered'
  return a?.visited ? 'visited' : 'unvisited'
}

export function counts(qs: Q[], answers: Record<string, Answer>, subs: Record<string, number> = {}) {
  const answered = qs.filter((q) => isAnswered(q, answers[q.id], subs[q.id] ?? 0)).length
  return { answered, unanswered: qs.length - answered, review: qs.filter((q) => answers[q.id]?.review).length }
}

/** Questions the candidate has not yet submitted: MCQ-type = no option chosen; coding = no explicit submission. Mirrors the server rule. */
export function unsubmittedIds(qs: Q[], answers: Record<string, Answer>, subs: Record<string, number>): string[] {
  return qs.filter((q) => (q.type === 'mcq' ? !answers[q.id]?.value : !(subs[q.id] > 0))).map((q) => q.id)
}
