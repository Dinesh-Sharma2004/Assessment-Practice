import type { AttemptState, Card, RunRes, SubmitRes } from './types'

export class ApiFail extends Error {
  constructor(public status: number, public code: string, message: string) { super(message) }
}

async function call<T>(method: string, url: string, body?: unknown): Promise<T> {
  let r: Response
  try {
    r = await fetch(url, { method, headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined })
  } catch {
    throw new ApiFail(0, 'network', 'Cannot reach the server')
  }
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new ApiFail(r.status, data.error ?? 'error', data.message ?? `HTTP ${r.status}`)
  return data as T
}

export const api = {
  cards: () => call<Card[]>('GET', '/api/assessments'),
  start: (assessmentId: string, profile: string) => call<{ attemptId: string }>('POST', '/api/attempts', { assessmentId, profile }),
  attempt: (id: string) => call<AttemptState>('GET', `/api/attempts/${id}`),
  saveAnswer: (id: string, qid: string, patch: { value?: string | null; review?: boolean; visited?: boolean; clear?: boolean }) =>
    call<{ saved: boolean }>('PUT', `/api/attempts/${id}/answers/${qid}`, patch),
  run: (id: string, qid: string, code: string) => call<RunRes>('POST', `/api/attempts/${id}/questions/${qid}/run`, { code }),
  submit: (id: string, qid: string, code: string) => call<SubmitRes>('POST', `/api/attempts/${id}/questions/${qid}/submit`, { code }),
  finishSection: (id: string) => call<AttemptState>('POST', `/api/attempts/${id}/finish-section`),
  results: (id: string) => call<any>('GET', `/api/attempts/${id}/results`), // eslint-disable-line @typescript-eslint/no-explicit-any
}
