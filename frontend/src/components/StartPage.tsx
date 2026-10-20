import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, ApiFail } from '../api'
import type { Card } from '../types'

export function StartPage() {
  const { aid } = useParams()
  const [card, setCard] = useState<Card | null>(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()
  useEffect(() => { api.cards().then((l) => setCard(l.find((c) => c.id === aid) ?? null)) }, [aid])
  if (!card) return <div className="p-6">Loading…</div>
  const begin = async () => {
    setBusy(true)
    try { nav(`/attempt/${(await api.start(card.id, 'standard')).attemptId}`) }
    catch (e) { setErr(e instanceof ApiFail ? e.message : String(e)); setBusy(false) }
  }
  return (
    <div className="max-w-3xl mx-auto p-6 space-y-4">
      <Link to="/" className="text-sm text-emerald-700">← Dashboard</Link>
      <h1 className="text-2xl font-semibold">{card.title}</h1>
      <div className="text-sm text-slate-600">Difficulty: <b>{card.level}</b> · {card.questionCount} questions · {card.totalMarks} marks · {Math.round(card.timing.totalSeconds / 60)} minutes{card.hintsEnabled ? ' · hints available' : ' · no hints'}</div>
      <table className="w-full text-sm bg-white border border-slate-200" data-testid="schedule">
        <thead className="bg-slate-100"><tr><th className="text-left p-2">Section</th><th className="text-left p-2">Questions</th><th className="text-left p-2">Marks</th><th className="text-left p-2">Time</th></tr></thead>
        <tbody>{card.sections.map((s) => <tr key={s.key} className="border-t border-slate-200"><td className="p-2">{s.title.replace(/^Section \d+: /, '')}</td><td className="p-2">{s.questions}</td><td className="p-2">{s.marks}</td><td className="p-2">{s.seconds / 60} min</td></tr>)}</tbody>
      </table>
      <div className="bg-white border border-slate-200 rounded p-4 text-sm space-y-2">
        <h2 className="font-semibold">Instructions</h2>
        <ul className="list-disc pl-5 space-y-1">
          <li>Sections run in a fixed order and each has its own timer. You can move freely between the questions of the <b>active</b> section only.</li>
          <li><b>Finishing early:</b> when every question of a section is submitted (MCQ-type: an option chosen; coding: <b>Submit</b> pressed) the <b>Finish Section</b> button unlocks. The next section then starts immediately with its full time, and the finished section is locked for good. After the last section the same button reads <b>End Test</b>.</li>
          <li>When a section's time runs out it is saved, graded and locked automatically and the next one starts. Timers live on the server: refreshing never resets them.</li>
          <li>For coding questions use <b>Run</b> to try the public samples and <b>Submit</b> to grade against all tests. The latest submission counts; a final draft you never submitted is auto-graded when time ends.</li>
          {card.hintsEnabled && <li>Every question has a <b>hint</b> button (formula hints for MCQs and aptitude, step-by-step hints for coding).</li>}
          <li>Correct answers, explanations and reference solutions appear only after the whole attempt ends.</li>
        </ul>
      </div>
      {err && <div role="alert" className="text-red-700">{err}</div>}
      <p className="text-sm text-slate-600">The timer starts only when you click the button below.</p>
      <button className="btn btn-primary" disabled={busy} onClick={begin} data-testid="begin">Start Assessment</button>
    </div>
  )
}
