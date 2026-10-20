import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, ApiFail } from '../api'
import { fmtClock } from '../util'
import { ChartView } from './ChartView'
import { Statement } from './Statement'

/* eslint-disable @typescript-eslint/no-explicit-any */
export function Results() {
  const { id } = useParams() as { id: string }
  const nav = useNavigate()
  const [r, setR] = useState<any>(null)
  const [err, setErr] = useState('')
  useEffect(() => {
    api.results(id).then(setR).catch((e) => {
      if (e instanceof ApiFail && e.code === 'not_finished') nav(`/attempt/${id}`, { replace: true })   // guard: no peeking mid-attempt
      else setErr(e.message)
    })
  }, [id, nav])
  if (err) return <div className="p-6 text-red-700" role="alert">{err}</div>
  if (!r) return <div className="p-6">Loading results…</div>
  const strengths = r.topics.filter((t: any) => t.percent >= 70), weak = [...r.topics].filter((t: any) => t.percent < 50).sort((a: any, b: any) => a.percent - b.percent)
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-5">
      <Link to="/" className="text-sm text-emerald-700">← Dashboard</Link>
      <div className="flex flex-wrap items-end gap-4">
        <div><h1 className="text-2xl font-semibold">{r.title}</h1><div className="text-sm text-slate-600">attempt</div></div>
        <div className="ml-auto text-right"><div className="text-3xl font-bold" data-testid="total-score">{r.total} / {r.max}</div><div className="text-sm" data-testid="total-percent">{r.percent}%</div></div>
        <Link className="btn btn-primary" to={`/start/${r.assessmentId}`} data-testid="retake">Retake</Link>
      </div>
      <table className="w-full text-sm bg-white border border-slate-200">
        <thead className="bg-slate-100"><tr>{['Section', 'Score', '%', 'Attempted', 'Unanswered', 'Marked review', 'Time allotted / used'].map((h) => <th key={h} className="text-left p-2">{h}</th>)}</tr></thead>
        <tbody>{r.sections.map((s: any) => (
          <tr key={s.key} className="border-t border-slate-200"><td className="p-2">{s.title}</td><td className="p-2">{s.score} / {s.max}</td><td className="p-2">{s.percent}%</td>
            <td className="p-2">{s.attempted}</td><td className="p-2">{s.unanswered}</td><td className="p-2">{s.reviewed}</td>
            <td className="p-2">{fmtClock(s.timeAllottedSeconds)} / {fmtClock(s.timeSpentSeconds)} <span className="text-xs text-slate-500">{s.finishedEarly ? '(finished early)' : '(time ran out)'}</span></td></tr>))}</tbody>
      </table>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white border border-slate-200 p-3 rounded"><h2 className="font-semibold text-sm mb-1">Strengths (≥ 70%)</h2>{strengths.length ? strengths.map((t: any) => <div key={t.tag} className="text-sm">{t.tag} — {t.percent}% ({t.questions} q)</div>) : <div className="text-sm text-slate-500">None yet</div>}</div>
        <div className="bg-white border border-slate-200 p-3 rounded"><h2 className="font-semibold text-sm mb-1">Weaknesses (&lt; 50%)</h2>{weak.length ? weak.slice(0, 15).map((t: any) => <div key={t.tag} className="text-sm">{t.tag} — {t.percent}% ({t.questions} q)</div>) : <div className="text-sm text-slate-500">None</div>}</div>
      </div>
      <h2 className="font-semibold">Question review</h2>
      {r.questions.map((q: any) => (
        <details key={q.id} className="bg-white border border-slate-200 rounded p-3" data-testid={`review-${q.id}`}>
          <summary className="cursor-pointer text-sm"><b>{q.id}</b> — {q.title} <span className={q.earned >= q.marks ? 'text-emerald-700' : q.earned > 0 ? 'text-amber-700' : 'text-red-700'}>{q.earned}/{q.marks}</span>
            {!q.attempted && <span className="text-slate-500"> (unanswered)</span>}{q.review && <span className="text-amber-600"> ⚑</span>}</summary>
          <div className="mt-2 space-y-2">
            {q.charts && q.charts.map((c: any, i: number) => <ChartView key={i} chart={c} index={i} />)}
            <Statement text={q.statement} />
            {q.type === 'mcq' ? (
              <>
                <ul className="text-sm">{q.options.map((o: any) => <li key={o.id} className={o.id === q.correct ? 'text-emerald-700 font-semibold' : o.id === q.selected ? 'text-red-700' : ''}>{o.id}. {o.text} {o.id === q.correct && '✔ correct'} {o.id === q.selected && o.id !== q.correct && '← your answer'}</li>)}</ul>
              </>
            ) : (
              <>
                <div className="text-sm">Tests passed: {q.testsPassed}/{q.testsTotal} ({q.source === 'draft' ? 'unsubmitted draft auto-graded' : q.source === 'submission' ? 'latest submission' : 'no submission'})</div>
                {q.gradingError && <div role="alert" className="text-red-700 text-sm">Grading failed: {q.gradingError}</div>}
                <div className="flex flex-wrap gap-1">{q.tests.map((t: any) => <span key={t.id} title={`${t.visibility}: ${t.description} (weight ${t.weight})`} className={`text-xs px-1.5 rounded ${t.passed ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>{t.visibility[0].toUpperCase()}{t.passed ? '✔' : `✘ ${t.kind}`}</span>)}</div>
                {q.submittedCode && <details><summary className="text-sm cursor-pointer">Your code</summary><pre className="text-xs bg-slate-100 p-2 rounded overflow-x-auto">{q.submittedCode}</pre></details>}
                <details><summary className="text-sm cursor-pointer">Reference solution</summary><pre className="text-xs bg-slate-100 p-2 rounded overflow-x-auto">{q.referenceSolution}</pre></details>
              </>
            )}
            <div className="text-sm"><b>Explanation:</b> {q.explanation}</div>
          </div>
        </details>
      ))}
    </div>
  )
}
