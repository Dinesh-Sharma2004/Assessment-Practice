import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { sql, SQLite } from '@codemirror/lang-sql'

export function Editor({ value, onChange, lang, testId }: { value: string; onChange: (v: string) => void; lang: 'sql' | 'python'; testId: string }) {
  return (
    <div data-testid={testId} className="border border-slate-300 rounded overflow-hidden bg-white">
      <CodeMirror value={value} height="320px" onChange={onChange} extensions={[lang === 'sql' ? sql({ dialect: SQLite }) : python()]}
        basicSetup={{ lineNumbers: true, foldGutter: false, highlightActiveLine: true, indentOnInput: true }} />
    </div>
  )
}
