export type DF = { columns: string[]; dtypes?: Record<string, string>; data: unknown[][] }

export function Table({ columns, rows, max = 25 }: { columns: string[]; rows: unknown[][]; max?: number }) {
  return (
    <div className="overflow-x-auto">
      <table className="text-xs border-collapse">
        <thead><tr>{columns.map((c) => <th key={c} className="border border-slate-300 bg-slate-100 px-2 py-0.5 text-left">{c}</th>)}</tr></thead>
        <tbody>
          {rows.slice(0, max).map((r, i) => (
            <tr key={i}>{r.map((v, j) => <td key={j} className="border border-slate-300 px-2 py-0.5 font-mono">{v === null ? <i className="text-slate-400">NULL</i> : String(v)}</td>)}</tr>
          ))}
        </tbody>
      </table>
      {rows.length > max && <div className="text-xs text-slate-500">… {rows.length - max} more rows</div>}
      {rows.length === 0 && columns.length > 0 && <div className="text-xs text-slate-500">(no rows)</div>}
    </div>
  )
}

export function DFView({ df, title }: { df: DF; title?: string }) {
  return (
    <div className="mb-2">
      {title && <div className="text-xs font-semibold text-slate-600">{title}</div>}
      <Table columns={df.columns.map((c) => `${c} : ${df.dtypes?.[c] ?? ''}`)} rows={df.data} max={12} />
    </div>
  )
}
