import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import type { Card } from '../types'

export function Dashboard() {
  const [cards, setCards] = useState<Card[] | null>(null)
  const [err, setErr] = useState('')
  const nav = useNavigate()
  useEffect(() => { api.cards().then(setCards).catch((e) => setErr(e.message)) }, [])
  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-semibold">Data Science Intern — Mock Assessments</h1>
      <p className="text-sm text-slate-600 mb-4">Independent practice material, not official Nasdaq questions. Sections are timed and locked in order: MCQs → SQL → Pandas → DSA.</p>
      {err && <div role="alert" className="bg-red-50 text-red-700 p-2 rounded">{err}</div>}
      {!cards && !err && <p>Loading…</p>}
      <div className="grid gap-4 md:grid-cols-2">
        {cards?.map((c) => (
          <div key={c.id} data-testid={`card-${c.id}`} className="bg-white rounded border border-slate-200 p-4 flex flex-col gap-2">
            <h2 className="font-semibold">{c.title}</h2>
            <p className="text-sm text-slate-600 flex-1">{c.description}</p>
            <div className="text-xs text-slate-600 flex flex-wrap gap-x-4 gap-y-1">
              <span>{c.questionCount} questions</span><span>{c.totalMarks} marks</span><span data-testid={`level-${c.id}`}>Difficulty: <b>{c.level}</b></span>
              <span>Total time {Math.round(c.timing.totalSeconds / 60)} min</span>{c.hintsEnabled && <span>💡 Hints available</span>}
            </div>
            <div className="text-xs text-slate-600">{c.sections.map((x) => `${x.title.replace(/^Section \d+: /, '').split(' (')[0]}: ${x.questions} q · ${x.seconds / 60} min`).join('  |  ')}</div>
            <div className="text-xs bg-slate-50 rounded p-2 flex flex-wrap gap-x-4">
              <span>Attempts: {c.attempts}</span>
              <span>Latest: {c.latestScore != null ? `${c.latestScore} / ${c.totalMarks}` : '—'}</span>
              <span>Best: {c.bestScore != null ? `${c.bestScore} / ${c.totalMarks}` : '—'}</span>
              <span>Status: {c.activeAttemptId ? 'In progress' : c.completedAttempts ? 'Completed' : 'Not started'}</span>
            </div>
            <div className="flex gap-2">
              {c.activeAttemptId
                ? <button className="btn btn-primary" onClick={() => nav(`/attempt/${c.activeAttemptId}`)}>Resume Attempt</button>
                : <Link className="btn btn-primary" to={`/start/${c.id}`} data-testid={`start-${c.id}`}>Start Assessment</Link>}
              {c.latestAttemptId && <Link className="btn btn-ghost" to={`/results/${c.latestAttemptId}`}>View Results</Link>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
