export type Section = { index: number; key: 'mcq' | 'apt' | 'da' | 'sql' | 'pandas' | 'dsa'; status: 'locked' | 'active' | 'finalized'; durationSeconds: number; startedAt: number | null; deadline: number | null; remainingSeconds: number | null }
export type Answer = { value: string | null; review: boolean; visited: boolean }
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Q = Record<string, any> & { id: string; type: 'mcq' | 'sql' | 'pandas' | 'dsa'; marks: number; statement: string }
export type AttemptState = {
  id: string; assessmentId: string; title: string; profile: string; hintsEnabled: boolean; status: 'active' | 'completed'; serverNow: number
  currentSection: number | null; totalMarks: number; sections: Section[]; questions: Q[]; answers: Record<string, Answer>; submissionCounts?: Record<string, number>
  unsubmitted?: string[]; canFinish?: boolean; isLastSection?: boolean
}
export type Card = {
  id: string; title: string; description: string; difficulty: string; level: string; hintsEnabled: boolean; questionCount: number; totalMarks: number
  sections: { key: string; title: string; questions: number; marks: number; seconds: number }[]
  timing: { totalSeconds: number; sectionSeconds: Record<string, number> }
  attempts: number; completedAttempts: number; activeAttemptId: string | null; latestScore: number | null; latestAttemptId: string | null; bestScore: number | null
}
export type TestRes = { id: string; visibility: 'public' | 'hidden'; passed: boolean; kind: string; seconds: number; message?: string; stdout?: string }
export type RunRes = { tests: TestRes[]; passed: number; total: number }
export type SubmitRes = { earned: number; marks: number; publicPassed: number; publicTotal: number; hiddenPassed: number; hiddenTotal: number; tests: TestRes[] }
