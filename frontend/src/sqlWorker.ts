/// <reference lib="webworker" />
import initSqlJs from 'sql.js/dist/sql-wasm.js'
import wasmUrl from 'sql.js/dist/sql-wasm.wasm?url'

export type SqlJob = { id: number; schemaSql: string; dataSql: string; query: string; subtype: 'select' | 'update'; checkQueries: { id: string; sql: string }[] }
export type SqlTable = { title: string; columns: string[]; rows: unknown[][] }
export type SqlOut = { id: number; tables: SqlTable[]; error?: string; changes?: number }

const sqlReady = initSqlJs({ locateFile: () => wasmUrl })

self.onmessage = async (ev: MessageEvent<SqlJob>) => {
  const job = ev.data
  const out: SqlOut = { id: job.id, tables: [] }
  try {
    const SQL = await sqlReady
    const db = new SQL.Database()                       // brand-new database for every run: UPDATEs can never leak between runs
    try {
      db.exec(job.schemaSql)
      db.exec(job.dataSql)
      if (job.subtype === 'select') {
        const res = db.exec(job.query)
        out.tables = res.map((r, i) => ({ title: `Result ${i + 1}`, columns: r.columns, rows: r.values }))
        if (!res.length) out.tables = [{ title: 'Statement executed (no rows returned)', columns: [], rows: [] }]
      } else {
        db.exec(job.query)
        out.changes = db.getRowsModified()
        for (const cq of job.checkQueries) {
          const r = db.exec(cq.sql)[0]
          out.tables.push({ title: `State after your statements: ${cq.id}`, columns: r?.columns ?? [], rows: r?.values ?? [] })
        }
      }
    } finally {
      db.close()
    }
  } catch (e) {
    out.error = e instanceof Error ? e.message : String(e)
  }
  self.postMessage(out)
}
