import { useRef, useState } from 'react'
import { api, ApiFail } from '../api'
import type { Q, RunRes, SubmitRes, TestRes } from '../types'
import { Editor } from './Editor'
import { DFView, Table } from './DFTable'
import { HintBox } from './HintBox'
import { Statement } from './Statement'
import type { SqlJob, SqlOut } from '../sqlWorker'

function TestList({ tests, labels }: { tests: TestRes[]; labels: Record<string, string> }) {
  return (
    <ul className="space-y-1 text-sm" data-testid="test-list">
      {tests.map((t) => (
        <li key={t.id} className={t.passed ? 'text-emerald-700' : 'text-red-700'}>
          {t.passed ? '✔' : '✘'} {t.visibility === 'public' ? labels[t.id] ?? t.id : `Hidden test (${t.kind === 'ok' ? 'passed' : t.kind})`}
          {t.message && !t.passed && <pre className="bg-slate-100 text-slate-800 p-1 text-xs whitespace-pre-wrap rounded">{t.message}</pre>}
          {t.stdout && <pre className="bg-slate-100 text-slate-600 p-1 text-xs whitespace-pre-wrap rounded">stdout: {t.stdout}</pre>}
        </li>
      ))}
    </ul>
  )
}

export function CodeView({ q, attemptId, code, onCode, onSubmitted, locked }: {
  q: Q; attemptId: string; code: string; onCode: (v: string) => void; onSubmitted: () => void; locked: boolean
}) {
  const [busy, setBusy] = useState<string>('')
  const [run, setRun] = useState<RunRes | null>(null)
  const [sub, setSub] = useState<SubmitRes | null>(null)
  const [err, setErr] = useState('')
  const [sqlOut, setSqlOut] = useState<SqlOut | null>(null)
  const worker = useRef<Worker | null>(null)
  const jobId = useRef(0)
  const labels = Object.fromEntries((q.publicTests as { id: string; description: string }[]).map((t, i) => [t.id, `Public test ${i + 1}: ${t.description}`]))

  const guard = async (name: string, fn: () => Promise<void>) => {
    setBusy(name); setErr('')
    try { await fn() } catch (e) { setErr(e instanceof ApiFail ? `${e.message}` : String(e)) } finally { setBusy('') }
  }
  const runSql = () => guard('sql', () => new Promise<void>((resolve) => {
    if (!worker.current) worker.current = new Worker(new URL('../sqlWorker.ts', import.meta.url), { type: 'module' })
    const id = ++jobId.current
    const w = worker.current
    const timer = setTimeout(() => { w.terminate(); worker.current = null; setSqlOut({ id, tables: [], error: 'Query timed out after 10 s and was stopped.' }); resolve() }, 10000)
    w.onmessage = (ev: MessageEvent<SqlOut>) => { if (ev.data.id === id) { clearTimeout(timer); setSqlOut(ev.data); resolve() } }
    const job: SqlJob = { id, schemaSql: q.schemaSql, dataSql: q.sampleDataSql, query: code, subtype: q.subtype, checkQueries: q.checkQueries }
    w.postMessage(job)
  }))
  const runTests = () => guard('run', async () => { setRun(await api.run(attemptId, q.id, code)); setSub(null) })
  const submit = () => guard('submit', async () => { setSub(await api.submit(attemptId, q.id, code)); setRun(null); onSubmitted() })

  return (
    <div className="grid lg:grid-cols-2 gap-4 h-full">
      <div className="overflow-y-auto pr-2 max-h-[calc(100vh-190px)] space-y-3" data-testid="problem">
        <h2 className="text-lg font-semibold">{q.title} <span className="text-xs font-normal text-slate-500">({q.marks} marks · {q.difficulty})</span></h2>
        <Statement text={q.statement} />
        {q.outputSpec && <p className="text-xs text-slate-600"><b>Output:</b> {q.outputSpec}</p>}
        {q.hints && <HintBox hints={q.hints as string[]} storageKey={`hint:${attemptId}:${q.id}`} />}
        {q.type === 'sql' && (
          <>
            <div className="text-xs text-slate-600">This query uses <b>{q.tableCount} table{q.tableCount > 1 ? 's' : ''}</b>.</div>
            <details open><summary className="cursor-pointer font-semibold text-sm">Table descriptions</summary>
              {(q.tables as { name: string; description: string; columns: { name: string; type: string; description: string }[] }[]).map((t) => (
                <div key={t.name} className="text-xs mb-2"><b>{t.name}</b> — {t.description}
                  <ul className="pl-4 list-disc">{t.columns.map((c) => <li key={c.name}><code>{c.name}</code> {c.type} — {c.description}</li>)}</ul></div>))}
            </details>
            <div data-testid="sql-example" className="border border-slate-200 rounded bg-slate-50 p-2 space-y-2">
              <div className="font-semibold text-sm">Example</div>
              {(q.sampleTables as { name: string; columns: string[]; rows: unknown[][] }[]).map((t) => (
                <div key={t.name}><div className="text-xs font-semibold">Input table: {t.name}</div><Table columns={t.columns} rows={t.rows} max={20} /></div>))}
              {q.subtype === 'select'
                ? <div><div className="text-xs font-semibold">Expected output</div><Table columns={q.sampleExpected.columns} rows={q.sampleExpected.rows} /></div>
                : Object.entries(q.sampleExpected as Record<string, { columns: string[]; rows: unknown[][] }>).map(([k, v]) => <div key={k}><div className="text-xs font-semibold">Expected table after the update: {k}</div><Table columns={v.columns} rows={v.rows} /></div>)}
              {q.walkthrough && <div className="text-sm"><b>How the result is obtained:</b> {q.walkthrough}</div>}
            </div>
            <details><summary className="cursor-pointer text-sm">Show the CREATE TABLE / INSERT script of the sample database</summary><pre className="text-xs bg-slate-100 p-2 rounded overflow-x-auto max-h-64">{q.schemaSql}{'\n\n'}{q.sampleDataSql}</pre></details>
          </>
        )}
        {q.type === 'pandas' && (
          <>
            <p className="text-xs"><b>Signature:</b> <code>{q.functionSignature}</code></p>
            {(q.inputs as { name: string; columns: { name: string; dtype: string; description: string }[] }[]).map((i) => (
              <div key={i.name} className="text-xs"><b>Input DataFrame <code>{i.name}</code></b>
                <ul className="pl-4 list-disc">{i.columns.map((c) => <li key={c.name}><code>{c.name}</code> ({c.dtype}) — {c.description}</li>)}</ul></div>))}
            {q.walkthrough && <div className="text-sm border border-slate-200 rounded bg-slate-50 p-2" data-testid="walkthrough"><b>Example explained:</b> {q.walkthrough}</div>}
            <details open><summary className="cursor-pointer font-semibold text-sm">Public samples (inputs and expected output)</summary>
              {(q.publicTests as { id: string; description: string; inputs: Record<string, never>; params: Record<string, unknown>; expected: never }[]).map((t) => (
                <div key={t.id} className="border-t border-slate-200 py-2"><div className="text-xs italic">{t.description}</div>
                  {Object.entries(t.inputs).map(([n, df]) => <DFView key={n} df={df} title={`input: ${n}`} />)}
                  {Object.keys(t.params).length > 0 && <div className="text-xs">params: <code>{JSON.stringify(t.params)}</code></div>}
                  <DFView df={t.expected} title="expected output" /></div>))}
            </details>
          </>
        )}
        {q.type === 'dsa' && (
          <>
            <p className="text-xs"><b>Signature:</b> <code>{q.functionSignature}</code></p>
            <div className="text-xs"><b>Constraints</b><ul className="pl-4 list-disc">{(q.constraints as string[]).map((c) => <li key={c}>{c}</li>)}</ul></div>
            <div className="text-sm" data-testid="dsa-examples"><b>Examples</b>{(q.examples as { description: string; input: Record<string, unknown>; output: unknown; steps?: string[] }[]).map((e, i) => (
              <div key={i} className="border border-slate-200 rounded bg-slate-50 p-2 my-2">
                <div className="font-semibold">Example {i + 1}: {e.description}</div>
                <table className="text-xs my-1"><tbody>{Object.entries(e.input).map(([k, v]) => <tr key={k}><td className="pr-3 font-mono align-top">{k}</td><td className="font-mono">{JSON.stringify(v)}</td></tr>)}<tr><td className="pr-3 font-semibold align-top">output</td><td className="font-mono font-semibold">{JSON.stringify(e.output)}</td></tr></tbody></table>
                {e.steps && <ol className="list-decimal pl-5 text-sm space-y-0.5">{e.steps.map((st, k) => <li key={k}>{st}</li>)}</ol>}
              </div>))}</div>
            <p className="text-xs text-slate-600">Target complexity: {q.expectedComplexity}. Time limit per test: {q.timeLimitSecondsPerTest}s (hard stop at 3×).</p>
          </>
        )}
      </div>
      <div className="space-y-2">
        <Editor value={code} onChange={onCode} lang={q.type === 'sql' ? 'sql' : 'python'} testId="editor" />
        <div className="flex flex-wrap gap-2 items-center">
          {q.type === 'sql' && <button className="btn btn-ghost" onClick={runSql} disabled={!!busy || locked} data-testid="run-sql">{busy === 'sql' ? 'Running…' : 'Run Query (sample DB)'}</button>}
          <button className="btn btn-ghost" onClick={runTests} disabled={!!busy || locked} data-testid="run-tests">{busy === 'run' ? 'Running…' : 'Run Public Tests'}</button>
          <button className="btn btn-primary" onClick={submit} disabled={!!busy || locked} data-testid="submit-code">{busy === 'submit' ? 'Grading…' : 'Submit'}</button>
          <button className="btn btn-ghost" onClick={() => onCode(q.starterQuery ?? q.starterCode)} disabled={locked}>Reset to starter</button>
        </div>
        {err && <div role="alert" data-testid="code-error" className="bg-red-50 text-red-700 p-2 rounded text-sm">{err}</div>}
        {sqlOut && (
          <div className="bg-white border border-slate-200 rounded p-2" data-testid="sql-output">
            {sqlOut.error
              ? <pre className="text-red-700 text-xs whitespace-pre-wrap" data-testid="sql-error">SQL error: {sqlOut.error}</pre>
              : <>{sqlOut.changes !== undefined && <div className="text-xs mb-1">{sqlOut.changes} row(s) modified in the disposable sample database.</div>}
                {sqlOut.tables.map((t) => <div key={t.title} className="mb-2"><div className="text-xs font-semibold">{t.title}</div><Table columns={t.columns} rows={t.rows} /></div>)}</>}
          </div>
        )}
        {run && <div className="bg-white border border-slate-200 rounded p-2" data-testid="run-result"><div className="font-semibold text-sm mb-1">Public tests: {run.passed}/{run.total} passed</div><TestList tests={run.tests} labels={labels} /></div>}
        {sub && (
          <div className="bg-white border border-slate-200 rounded p-2" data-testid="submit-result">
            <div className="font-semibold text-sm">Submitted — score {sub.earned} / {sub.marks}</div>
            <div className="text-xs mb-1">Public {sub.publicPassed}/{sub.publicTotal} · Hidden {sub.hiddenPassed}/{sub.hiddenTotal} (details hidden until the attempt ends). The latest submission is the one that counts.</div>
            <TestList tests={sub.tests} labels={labels} />
          </div>
        )}
      </div>
    </div>
  )
}
