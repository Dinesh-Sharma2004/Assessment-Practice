import { Fragment } from 'react'

// Minimal, safe Markdown renderer (no HTML injection): paragraphs, bullet lists, fenced code, inline `code` and **bold**.
function inline(text: string) {
  return text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).map((p, i) =>
    p.startsWith('`') ? <code key={i}>{p.slice(1, -1)}</code> : p.startsWith('**') ? <strong key={i}>{p.slice(2, -2)}</strong> : <Fragment key={i}>{p}</Fragment>)
}

export function Statement({ text }: { text: string }) {
  const blocks: React.ReactNode[] = []
  const parts = text.split(/```[a-z]*\n([\s\S]*?)```/g)
  parts.forEach((part, i) => {
    if (i % 2 === 1) { blocks.push(<pre key={i}>{part}</pre>); return }
    let list: string[] = []
    const flush = () => { if (list.length) { blocks.push(<ul key={`${i}-l${blocks.length}`}>{list.map((l, k) => <li key={k}>{inline(l)}</li>)}</ul>); list = [] } }
    part.split('\n').forEach((line) => {
      if (/^\s*[*-] /.test(line)) list.push(line.replace(/^\s*[*-] /, ''))
      else { flush(); if (line.trim()) blocks.push(<p key={`${i}-${blocks.length}`}>{inline(line)}</p>) }
    })
    flush()
  })
  return <div className="statement text-sm leading-6">{blocks}</div>
}
