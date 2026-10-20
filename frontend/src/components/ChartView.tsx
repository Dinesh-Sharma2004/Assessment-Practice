import { fmtNum, pieAngles, ticks } from '../chartMath'

/* eslint-disable @typescript-eslint/no-explicit-any */
const COLORS = ['#2563eb', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#14b8a6']
const W = 600, H = 320, M = { l: 56, r: 16, t: 34, b: 52 }

function Legend({ names }: { names: string[] }) {
  return (
    <div className="flex flex-wrap gap-3 text-xs mt-1 justify-center">
      {names.map((n, i) => <span key={n} className="inline-flex items-center gap-1"><span className="inline-block w-3 h-3" style={{ background: COLORS[i % COLORS.length] }} />{n}</span>)}
    </div>
  )
}

function Axes({ chart, max, cats, children }: { chart: any; max: number; cats: string[]; children: React.ReactNode }) {
  const tk = ticks(max), top = tk[tk.length - 1]
  const y = (v: number) => H - M.b - ((H - M.t - M.b) * v) / top
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={chart.title} className="w-full max-w-xl bg-white border border-slate-200 rounded">
      <text x={W / 2} y={18} textAnchor="middle" fontSize="13" fontWeight="600">{chart.title}</text>
      {tk.map((t) => (<g key={t}><line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} stroke="#e2e8f0" /><text x={M.l - 6} y={y(t) + 4} textAnchor="end" fontSize="10" fill="#475569">{fmtNum(t)}</text></g>))}
      <line x1={M.l} x2={M.l} y1={M.t} y2={H - M.b} stroke="#64748b" /><line x1={M.l} x2={W - M.r} y1={H - M.b} y2={H - M.b} stroke="#64748b" />
      {cats.map((c, i) => <text key={c} x={M.l + ((W - M.l - M.r) * (i + 0.5)) / cats.length} y={H - M.b + 16} textAnchor="middle" fontSize="11" fill="#334155">{c}</text>)}
      <text x={W / 2} y={H - 8} textAnchor="middle" fontSize="11" fill="#475569">{chart.xLabel}</text>
      <text transform={`rotate(-90 14 ${H / 2})`} x={14} y={H / 2} textAnchor="middle" fontSize="11" fill="#475569">{chart.yLabel}</text>
      {children}
    </svg>
  )
}

function Bars({ chart, stacked }: { chart: any; stacked: boolean }) {
  const cats: string[] = chart.categories, series: { name: string; values: number[] }[] = chart.series
  const max = stacked ? Math.max(...cats.map((_, i) => series.reduce((a, s) => a + s.values[i], 0))) : Math.max(...series.flatMap((s) => s.values))
  const top = ticks(max)[5]
  const y = (v: number) => H - M.b - ((H - M.t - M.b) * v) / top
  const band = (W - M.l - M.r) / cats.length
  return (
    <Axes chart={chart} max={max} cats={cats}>
      {cats.map((c, i) => {
        if (stacked) {
          let acc = 0
          return series.map((s, k) => {
            const v = s.values[i], y0 = y(acc), y1 = y(acc + v); acc += v
            return <g key={`${c}${k}`}><rect x={M.l + band * i + band * 0.2} width={band * 0.6} y={y1} height={y0 - y1} fill={COLORS[k % 6]} /><text x={M.l + band * (i + 0.5)} y={(y0 + y1) / 2 + 4} textAnchor="middle" fontSize="10" fill="#fff">{fmtNum(v)}</text></g>
          })
        }
        const w = (band * 0.7) / series.length
        return series.map((s, k) => (
          <g key={`${c}${k}`}><rect x={M.l + band * i + band * 0.15 + w * k} width={w} y={y(s.values[i])} height={H - M.b - y(s.values[i])} fill={COLORS[k % 6]} />
            <text x={M.l + band * i + band * 0.15 + w * (k + 0.5)} y={y(s.values[i]) - 4} textAnchor="middle" fontSize="10" fill="#0f172a">{fmtNum(s.values[i])}</text></g>
        ))
      })}
    </Axes>
  )
}

function Lines({ chart }: { chart: any }) {
  const cats: string[] = chart.categories, series: { name: string; values: number[] }[] = chart.series
  const max = Math.max(...series.flatMap((s) => s.values)), top = ticks(max)[5]
  const x = (i: number) => M.l + ((W - M.l - M.r) * (i + 0.5)) / cats.length
  const y = (v: number) => H - M.b - ((H - M.t - M.b) * v) / top
  return (
    <Axes chart={chart} max={max} cats={cats}>
      {series.map((s, k) => (
        <g key={s.name}><polyline fill="none" stroke={COLORS[k % 6]} strokeWidth="2" points={s.values.map((v, i) => `${x(i)},${y(v)}`).join(' ')} />
          {s.values.map((v, i) => <g key={i}><circle cx={x(i)} cy={y(v)} r="3.5" fill={COLORS[k % 6]} /><text x={x(i)} y={y(v) - 8} textAnchor="middle" fontSize="10" fill="#0f172a">{fmtNum(v)}</text></g>)}</g>
      ))}
    </Axes>
  )
}

function Scatter({ chart }: { chart: any }) {
  const pts: { x: number; y: number }[] = chart.series[0].points
  const xmax = Math.max(...pts.map((p) => p.x)), ymax = Math.max(...pts.map((p) => p.y)), xt = ticks(xmax), yt = ticks(ymax)
  const x = (v: number) => M.l + ((W - M.l - M.r) * v) / xt[5], y = (v: number) => H - M.b - ((H - M.t - M.b) * v) / yt[5]
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={chart.title} className="w-full max-w-xl bg-white border border-slate-200 rounded">
      <text x={W / 2} y={18} textAnchor="middle" fontSize="13" fontWeight="600">{chart.title}</text>
      {yt.map((t) => <g key={`y${t}`}><line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} stroke="#e2e8f0" /><text x={M.l - 6} y={y(t) + 4} textAnchor="end" fontSize="10" fill="#475569">{fmtNum(t)}</text></g>)}
      {xt.map((t) => <text key={`x${t}`} x={x(t)} y={H - M.b + 16} textAnchor="middle" fontSize="10" fill="#475569">{fmtNum(t)}</text>)}
      <line x1={M.l} x2={M.l} y1={M.t} y2={H - M.b} stroke="#64748b" /><line x1={M.l} x2={W - M.r} y1={H - M.b} y2={H - M.b} stroke="#64748b" />
      {pts.map((p, i) => <g key={i}><circle cx={x(p.x)} cy={y(p.y)} r="4.5" fill={COLORS[0]} opacity="0.85" /><text x={x(p.x) + 7} y={y(p.y) - 6} fontSize="10" fill="#0f172a">({p.x}, {p.y})</text></g>)}
      <text x={W / 2} y={H - 8} textAnchor="middle" fontSize="11" fill="#475569">{chart.xLabel}</text>
      <text transform={`rotate(-90 14 ${H / 2})`} x={14} y={H / 2} textAnchor="middle" fontSize="11" fill="#475569">{chart.yLabel}</text>
    </svg>
  )
}

function Pie({ chart }: { chart: any }) {
  const sl: { label: string; value: number }[] = chart.slices, ang = pieAngles(sl.map((s) => s.value)), cx = 170, cy = 165, r = 110
  const pt = (a: number, rr = r) => [cx + rr * Math.cos(a), cy + rr * Math.sin(a)]
  return (
    <svg viewBox="0 0 560 330" role="img" aria-label={chart.title} className="w-full max-w-xl bg-white border border-slate-200 rounded">
      <text x={280} y={18} textAnchor="middle" fontSize="13" fontWeight="600">{chart.title}</text>
      {ang.map((a, i) => {
        const [x0, y0] = pt(a.start), [x1, y1] = pt(a.end), large = a.end - a.start > Math.PI ? 1 : 0, [lx, ly] = pt((a.start + a.end) / 2, r * 0.62)
        return <g key={sl[i].label}><path d={`M${cx},${cy} L${x0},${y0} A${r},${r} 0 ${large} 1 ${x1},${y1} Z`} fill={COLORS[i % 6]} stroke="#fff" /><text x={lx} y={ly} textAnchor="middle" fontSize="12" fill="#fff" fontWeight="600">{sl[i].value}%</text></g>
      })}
      {sl.map((s, i) => <g key={s.label}><rect x={350} y={70 + i * 26} width="14" height="14" fill={COLORS[i % 6]} /><text x={372} y={82 + i * 26} fontSize="13">{s.label}</text></g>)}
    </svg>
  )
}

function DataTable({ columns, rows }: { columns: string[]; rows: unknown[][] }) {
  return (
    <table className="text-xs border-collapse bg-white"><thead><tr>{columns.map((c) => <th key={c} className="border border-slate-300 bg-slate-100 px-2 py-1 text-left">{c}</th>)}</tr></thead>
      <tbody>{rows.map((r, i) => <tr key={i}>{r.map((v, j) => <td key={j} className="border border-slate-300 px-2 py-1">{String(v)}</td>)}</tr>)}</tbody></table>
  )
}

export function ChartView({ chart, index }: { chart: any; index: number }) {
  let body: React.ReactNode, names: string[] = [], tableCols: string[] = [], tableRows: unknown[][] = []
  switch (chart.type) {
    case 'bar': case 'grouped': body = <Bars chart={chart} stacked={false} />; break
    case 'stacked': body = <Bars chart={chart} stacked />; break
    case 'line': body = <Lines chart={chart} />; break
    case 'scatter': body = <Scatter chart={chart} />; break
    case 'pie': body = <Pie chart={chart} />; break
    case 'table': return (<div className="my-3" data-testid={`chart-${index}`}><div className="text-sm font-semibold mb-1">{chart.title}</div><DataTable columns={chart.columns} rows={chart.rows} /></div>)
    default: body = null
  }
  if (chart.series && chart.categories) {
    names = chart.series.map((s: any) => s.name); tableCols = [chart.xLabel, ...names]; tableRows = chart.categories.map((c: string, i: number) => [c, ...chart.series.map((s: any) => s.values[i])])
  } else if (chart.type === 'scatter') {
    tableCols = [chart.xLabel, chart.yLabel]; tableRows = chart.series[0].points.map((p: any) => [p.x, p.y])
  } else if (chart.type === 'pie') {
    tableCols = ['Category', 'Percent']; tableRows = chart.slices.map((s: any) => [s.label, s.value])
  }
  return (
    <figure className="my-3" data-testid={`chart-${index}`}>
      {body}
      {names.length > 1 && chart.type !== 'stacked' && <Legend names={names} />}
      {chart.type === 'stacked' && <Legend names={names} />}
      <details className="mt-1"><summary className="text-xs text-slate-600 cursor-pointer">Show the plotted values as a table</summary><DataTable columns={tableCols} rows={tableRows} /></details>
    </figure>
  )
}
