import { useState } from 'react'

/** Progressive hints (LeetCode style): each click reveals the next hint. State is kept per question for the whole attempt. */
export function HintBox({ hints, storageKey }: { hints: string[]; storageKey: string }) {
  const read = () => { try { return Number(localStorage.getItem(storageKey) ?? 0) || 0 } catch { return 0 } }
  const [shown, setShown] = useState(read)
  const more = () => { const n = Math.min(hints.length, shown + 1); setShown(n); try { localStorage.setItem(storageKey, String(n)) } catch { /* private mode */ } }
  return (
    <div className="my-2" data-testid="hint-box">
      {shown > 0 && (
        <ol className="space-y-1 mb-2">
          {hints.slice(0, shown).map((h, i) => (
            <li key={i} data-testid={`hint-${i + 1}`} className="text-sm bg-amber-50 border border-amber-200 rounded px-2 py-1"><b>Hint {i + 1}{hints.length > 1 ? `/${hints.length}` : ''}:</b> {h}</li>
          ))}
        </ol>
      )}
      {shown < hints.length && (
        <button type="button" className="btn btn-ghost" data-testid="hint-btn" onClick={more}>💡 {shown === 0 ? 'Show hint' : 'Show next hint'}{hints.length > 1 ? ` (${shown}/${hints.length})` : ''}</button>
      )}
    </div>
  )
}
