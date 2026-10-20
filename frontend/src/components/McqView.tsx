import type { Q } from '../types'
import { ChartView } from './ChartView'
import { HintBox } from './HintBox'
import { Statement } from './Statement'

export function McqView({ q, value, onPick, locked, attemptId }: { q: Q; value: string | null; onPick: (v: string) => void; locked: boolean; attemptId: string }) {
  return (
    <div className="max-w-3xl">
      <div className="text-xs text-slate-500 mb-1">{q.topic} · {q.marks} marks · {q.difficulty}</div>
      {q.charts && (q.charts as unknown[]).map((c, i) => <ChartView key={i} chart={c} index={i} />)}
      <Statement text={q.statement} />
      {q.hints && <HintBox hints={q.hints as string[]} storageKey={`hint:${attemptId}:${q.id}`} />}
      <div className="mt-3 space-y-2" role="radiogroup">
        {(q.options as { id: string; text: string }[]).map((o) => (
          <label key={o.id} data-testid={`opt-${o.id}`} className={`flex gap-2 items-start bg-white border rounded p-2 cursor-pointer text-sm ${value === o.id ? 'border-emerald-600 ring-1 ring-emerald-600' : 'border-slate-200'}`}>
            <input type="radio" name={q.id} checked={value === o.id} disabled={locked} onChange={() => onPick(o.id)} />
            <span><b>{o.id}.</b> {o.text}</span>
          </label>
        ))}
      </div>
    </div>
  )
}
