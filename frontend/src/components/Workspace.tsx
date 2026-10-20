import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, ApiFail } from '../api'
import type { Answer, AttemptState } from '../types'
import { counts, fmtClock, paletteState, remainingFrom, SECTION_LABEL, starterOf, unsubmittedIds } from '../util'
import { CodeView } from './CodeView'
import { McqView } from './McqView'

const PAL: Record<string, string> = {
  answered: 'bg-emerald-600 text-white', review: 'bg-amber-400 text-slate-900', visited: 'bg-slate-300 text-slate-800', unvisited: 'bg-white text-slate-700 border border-slate-300',
}

export function Workspace() {
  const { id } = useParams() as { id: string }
  const nav = useNavigate()
  const [st, setSt] = useState<AttemptState | null>(null)
  const [answers, setAnswers] = useState<Record<string, Answer>>({})
  const [subs, setSubs] = useState<Record<string, number>>({})
  const [idx, setIdx] = useState(0)
  const [recv, setRecv] = useState(0)
  const [now, setNow] = useState(performance.now())
  const [notice, setNotice] = useState('')
  const [net, setNet] = useState('')
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [confirmFinish, setConfirmFinish] = useState(false)
  const [finishErr, setFinishErr] = useState('')
  const prevSection = useRef<number | null>(null)
  const early = useRef(false)
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({})

  const apply = useCallback((s: AttemptState) => {
    if (s.status === 'completed') { nav(`/results/${id}`, { replace: true }); return }
    if (prevSection.current !== null && prevSection.current !== s.currentSection) {
      const from = SECTION_LABEL[s.sections[prevSection.current].key], to = SECTION_LABEL[s.sections[s.currentSection!].key]
      setNotice(early.current ? `${from} finished. It is now locked and cannot be reopened. ${to} has started.` : `Time is up for ${from}. Your answers were saved and the section is locked. ${to} has started.`)
      early.current = false
      setIdx(0); setTimeout(() => setNotice(''), 8000)
    }
    if (prevSection.current !== s.currentSection) { setAnswers(s.answers); setSubs(s.submissionCounts ?? {}) }
    prevSection.current = s.currentSection
    setSt(s); setRecv(performance.now()); setNet('')
  }, [id, nav])

  const refresh = useCallback(async () => {
    try { apply(await api.attempt(id)) } catch (e) { setNet(e instanceof ApiFail && e.status === 404 ? 'Attempt not found' : 'Connection problem — retrying…') }
  }, [apply, id])

  useEffect(() => { refresh() }, [refresh])
  useEffect(() => { const t = setInterval(() => setNow(performance.now()), 250); return () => clearInterval(t) }, [])
  useEffect(() => { const t = setInterval(refresh, 5000); return () => clearInterval(t) }, [refresh])

  const sec = st?.sections.find((s) => s.status === 'active')
  const remaining = sec ? remainingFrom(sec.remainingSeconds ?? 0, recv, now) : 0
  useEffect(() => {                     // deadline reached: keep asking the server until it has switched sections
    if (!sec || remaining > 0) return
    const t = setInterval(refresh, 1000); refresh()
    return () => clearInterval(t)
  }, [sec?.index, remaining > 0, refresh])  // eslint-disable-line react-hooks/exhaustive-deps

  const qs = st?.questions ?? []
  const q = qs[idx]

  const persist = useCallback(async (qid: string, patch: Parameters<typeof api.saveAnswer>[2]) => {
    setSaveState('saving')
    try { await api.saveAnswer(id, qid, patch); setSaveState('saved') }
    catch (e) { setSaveState('error'); if (e instanceof ApiFail && (e.status === 409 || e.status === 403)) refresh() }
  }, [id, refresh])

  const patchLocal = (qid: string, p: Partial<Answer>) =>
    setAnswers((a) => ({ ...a, [qid]: { ...({ value: null, review: false, visited: false } as Answer), ...a[qid], ...p } }))

  const setValue = (qid: string, value: string | null, debounce: boolean) => {
    patchLocal(qid, { value })
    clearTimeout(timers.current[qid])
    const send = () => persist(qid, value === null ? { clear: true } : { value })
    if (debounce) { setSaveState('saving'); timers.current[qid] = setTimeout(send, 600) } else send()
  }
  const setFlag = (qid: string, p: { review?: boolean; visited?: boolean }) => { patchLocal(qid, p); persist(qid, p) }

  useEffect(() => { if (q && !answers[q.id]?.visited) setFlag(q.id, { visited: true }) }, [q?.id])  // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => { Object.values(timers.current).forEach(clearTimeout) }, [])

  const finish = async () => {
    setFinishErr('')
    try { early.current = true; apply(await api.finishSection(id)); setConfirmFinish(false) }
    catch (e) { early.current = false; setFinishErr(e instanceof ApiFail ? e.message : String(e)); refresh() }
  }

  if (!st) return <div className="p-6">{net || 'Loading attempt…'}</div>
  if (!q || !sec) return <div className="p-6">Loading…</div>
  const c = counts(qs, answers, subs)
  const a = answers[q.id]
  const low = remaining <= 300, critical = remaining <= 60
  const codeValue = a?.value ?? starterOf(q)
  const pending = unsubmittedIds(qs, answers, subs)
  const last = !!st.isLastSection
  const label = SECTION_LABEL[sec.key]

  return (
    <div className="h-full flex flex-col">
      <header className="bg-slate-800 text-white px-4 py-2 flex flex-wrap items-center gap-x-5 gap-y-1">
        <div className="font-semibold text-sm">{st.title}</div>
        <nav className="flex gap-1 flex-wrap" aria-label="Sections">
          {st.sections.map((s) => (
            <span key={s.key} data-testid={`sec-${s.key}`} data-status={s.status}
              className={`text-xs px-2 py-0.5 rounded ${s.status === 'active' ? 'bg-emerald-500 text-white' : s.status === 'finalized' ? 'bg-slate-600 text-slate-300 line-through' : 'bg-slate-700 text-slate-400'}`}>
              {SECTION_LABEL[s.key]}{s.status === 'locked' ? ' 🔒' : s.status === 'finalized' ? ' ✓' : ''}
            </span>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3 text-sm">
          <span data-testid="progress">Answered {c.answered}/{qs.length} · Unattempted {c.unanswered} · Review {c.review}</span>
          <button className={`btn ${pending.length === 0 ? 'btn-primary' : 'bg-slate-600 text-slate-300'}`} data-testid="finish-section" disabled={pending.length > 0}
            title={pending.length ? `Submit every question first (${pending.length} left)` : last ? 'End the test now' : 'Finish this section and start the next one'}
            onClick={() => { setFinishErr(''); setConfirmFinish(true) }}>
            {last ? 'End Test' : 'Finish Section'}{pending.length > 0 ? ` (${pending.length} left)` : ''}
          </button>
          <span data-testid="timer" aria-live="off" className={`font-mono text-base px-2 rounded ${critical ? 'bg-red-600 animate-pulse' : low ? 'bg-amber-500 text-slate-900' : 'bg-slate-700'}`}>{fmtClock(remaining)}</span>
        </div>
      </header>
      {notice && <div data-testid="transition-notice" role="status" className="bg-blue-600 text-white text-sm px-4 py-2">{notice}</div>}
      {net && <div role="alert" className="bg-red-600 text-white text-sm px-4 py-1">{net}</div>}
      {low && !notice && <div data-testid="time-warning" className={`text-sm px-4 py-1 ${critical ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-900'}`}>
        {critical ? 'Less than 1 minute left in this section!' : 'Less than 5 minutes left in this section.'} It will lock and save automatically.</div>}
      {confirmFinish && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" role="dialog" aria-modal="true" data-testid="finish-dialog">
          <div className="bg-white rounded p-5 max-w-md space-y-3">
            <h2 className="font-semibold">{last ? 'End the test?' : `Finish ${label}?`}</h2>
            <p className="text-sm">{last ? 'All sections are done. Your attempt will end now and the results and solutions will be shown.' : `All ${qs.length} questions are submitted. This section will be locked for good — you cannot come back to it — and the next section starts immediately with its full time.`}</p>
            {finishErr && <div role="alert" className="text-red-700 text-sm">{finishErr}</div>}
            <div className="flex justify-end gap-2"><button className="btn btn-ghost" onClick={() => setConfirmFinish(false)} data-testid="cancel-finish">Keep working</button>
              <button className="btn btn-primary" onClick={finish} data-testid="confirm-finish">{last ? 'End Test' : 'Finish and continue'}</button></div>
          </div>
        </div>
      )}
      <div className="flex-1 flex min-h-0">
        <aside className="w-48 shrink-0 bg-white border-r border-slate-200 p-3 overflow-y-auto" aria-label="Question palette">
          <div className="text-xs font-semibold mb-2">{label} questions</div>
          <div className="grid grid-cols-4 gap-1.5">
            {qs.map((x, i) => (
              <button key={x.id} data-testid={`pal-${i + 1}`} data-state={paletteState(x, answers[x.id], subs[x.id] ?? 0)} onClick={() => setIdx(i)}
                className={`h-8 text-xs rounded ${PAL[paletteState(x, answers[x.id], subs[x.id] ?? 0)]} ${i === idx ? 'outline outline-2 outline-blue-500' : ''}`}>{i + 1}</button>
            ))}
          </div>
          <ul className="text-[11px] mt-3 space-y-1 text-slate-600">
            <li><span className="inline-block w-3 h-3 bg-emerald-600 mr-1 align-middle" />Answered</li><li><span className="inline-block w-3 h-3 bg-amber-400 mr-1 align-middle" />Marked for review</li>
            <li><span className="inline-block w-3 h-3 bg-slate-300 mr-1 align-middle" />Visited, unanswered</li><li><span className="inline-block w-3 h-3 bg-white border border-slate-300 mr-1 align-middle" />Not visited</li>
          </ul>
          <p className="text-[11px] text-slate-500 mt-3">{q.type === 'mcq' ? 'Every question needs an answer before you can finish early.' : 'Every question needs a Submit before you can finish early.'}</p>
        </aside>
        <main className="flex-1 p-4 overflow-y-auto min-w-0">
          <div className="flex items-center gap-2 mb-3 text-sm">
            <span className="font-semibold">Question {idx + 1} of {qs.length}</span>
            <span data-testid="save-state" className="text-xs text-slate-500">{saveState === 'saving' ? 'Saving…' : saveState === 'saved' ? 'All changes saved' : saveState === 'error' ? 'Save failed' : ''}</span>
            <div className="ml-auto flex gap-2">
              <button className="btn btn-ghost" onClick={() => setFlag(q.id, { review: !a?.review })} data-testid="review">{a?.review ? 'Unmark review' : 'Mark for Review'}</button>
              <button className="btn btn-ghost" data-testid="clear" onClick={() => setValue(q.id, null, false)}>Clear Answer</button>
              <button className="btn btn-ghost" disabled={idx === 0} onClick={() => setIdx(idx - 1)} data-testid="prev">Previous</button>
              <button className="btn btn-ghost" disabled={idx === qs.length - 1} onClick={() => setIdx(idx + 1)} data-testid="next">Next</button>
            </div>
          </div>
          {q.type === 'mcq'
            ? <McqView key={q.id} q={q} value={a?.value ?? null} locked={remaining <= 0} attemptId={id} onPick={(v) => setValue(q.id, v, false)} />
            : <CodeView key={q.id} q={q} attemptId={id} code={codeValue} locked={remaining <= 0} onCode={(v) => setValue(q.id, v, true)}
                onSubmitted={() => setSubs((s) => ({ ...s, [q.id]: (s[q.id] ?? 0) + 1 }))} />}
        </main>
      </div>
    </div>
  )
}
