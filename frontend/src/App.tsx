import { useEffect, useState } from 'react'
import { getAgents, getHealth, reviserCallback, runAgent, validateOutput,
  type AgentInfo, type Health, type RunError, type RunResult } from './api'

function Pipeline({ agent }: { agent: AgentInfo }) {
  if (!agent.sub_agents.length) return null
  return (
    <div className="pipeline">
      <span className="hint">{agent.type}: runs in order</span>
      <div className="steps">
        {agent.sub_agents.map((s, i) => (
          <div key={s.name} className="stepwrap">
            {i > 0 && <span className="arrow">→</span>}
            <div className="step"><b>{s.name}</b><div className="hint">{s.tools?.length ? `tools: ${s.tools.join(', ')}` : 'no tools'}</div>
              <div className="hint">after_model: {s.callbacks?.after_model ?? '—'}</div></div>
          </div>
        ))}
      </div>
    </div>
  )
}

function Details({ a }: { a: AgentInfo }) {
  return (
    <details>
      <summary>{a.name}: instruction{a.instruction && a.instruction.length > 200 ? ` (${a.instruction.length} chars)` : ''}</summary>
      <pre className="instr">{a.instruction}</pre>
    </details>
  )
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [sel, setSel] = useState<string>('')
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<RunResult | null>(null)
  const [err, setErr] = useState<RunError | null>(null)
  const [raw, setRaw] = useState('{"capital": "Paris"}')
  const [vres, setVres] = useState<unknown>(null)
  const [cbText, setCbText] = useState('Hawaii and Japan are separated by the Pacific Ocean, so there is no direct train; travellers fly.\n---END-OF-EDIT---\n(scratch notes the reviser should not return)')
  const [cbRes, setCbRes] = useState<{ output: string } | null>(null)

  useEffect(() => {
    getHealth().then(setHealth)
    getAgents().then(a => { setAgents(a); setSel(a[0]?.id ?? ''); setMsg(a[0]?.example ?? '') })
  }, [])

  const agent = agents.find(a => a.id === sel)
  const pick = (a: AgentInfo) => { setSel(a.id!); setMsg(a.example ?? ''); setResult(null); setErr(null); setVres(null); setCbRes(null) }
  const run = async () => {
    setBusy(true); setErr(null); setResult(null)
    try { setResult(await runAgent(sel, msg)) } catch (e) { setErr(e as RunError) } finally { setBusy(false) }
  }
  const llm = health?.llm

  return (
    <div className="page">
      <header>
        <div><h1>🧭 Cymbal Travel · ADK Agent Console</h1>
          <div className="hint">Google Agent Development Kit agents, served by FastAPI. Model: <code>{health?.model}</code></div></div>
        {llm && <span className={`badge ${llm.configured ? 'ok' : 'off'}`}>
          {llm.configured ? `LLM: ${llm.backend}${llm.project ? ` (${llm.project})` : ''}` : 'LLM: not configured (offline mode)'}</span>}
      </header>
      {llm && !llm.configured && (
        <div className="banner">Offline mode: <b>{llm.reason}</b> You can still inspect every agent, validate the JSON schema and run the callbacks.
          "Run" will not call a model, and no output is simulated.</div>
      )}

      <div className="layout">
        <nav>
          {agents.map(a => (
            <button key={a.id} className={a.id === sel ? 'active' : ''} onClick={() => pick(a)}>
              <b>{a.title}</b><span>{a.id} · {a.type}</span>
            </button>
          ))}
        </nav>

        {agent && <main>
          <section className="card">
            <h2>{agent.title} <code>{agent.name}</code></h2>
            <p>{agent.description}</p>
            <div className="meta">
              <span>type <b>{agent.type}</b></span>
              {agent.model && <span>model <b>{agent.model}</b></span>}
              {agent.tools && <span>tools {agent.tools.length ? agent.tools.map(t => <b key={t} className="chip">{t}</b>) : <b>none</b>}</span>}
              {agent.output_schema && <span>output_schema <b className="chip">{String(agent.output_schema.title)}</b></span>}
              {agent.disallow_transfer_to_parent && <span><b>no transfers</b> (parent/peers)</span>}
            </div>
            <Pipeline agent={agent} />
            {agent.instruction !== undefined && <Details a={agent} />}
            {agent.sub_agents.map(s => <Details key={s.name} a={s} />)}
          </section>

          <section className="card">
            <h3>Run</h3>
            <textarea value={msg} onChange={e => setMsg(e.target.value)} rows={2} />
            <button className="primary" onClick={run} disabled={busy || !msg.trim()}>{busy ? 'Running…' : 'Run agent'}</button>
            {err && (
              <div className={`result ${err.status === 503 ? 'notrun' : 'error'}`}>
                <b>{err.status === 503 ? '⏸ Not run: no model credentials' : `⚠ Model call failed (${err.status}${err.error ? `, ${err.error}` : ''})`}</b>
                <div>{err.reason}</div>{err.note && <div className="hint">{err.note}</div>}
              </div>
            )}
            {result && (
              <div className="result">
                <div className="hint">{result.backend} · {result.model} · {result.elapsed_ms} ms</div>
                {result.events.map((ev, i) => (
                  <div key={i} className="event"><span className="author">{ev.author}{ev.final ? ' (final)' : ''}</span>
                    {ev.parts.map((p, j) => <pre key={j}>{p.kind === 'text' ? p.text : `${p.kind}: ${p.name} ${p.args ? JSON.stringify(p.args) : ''}`}</pre>)}
                  </div>
                ))}
              </div>
            )}
          </section>

          {agent.output_schema && (
            <section className="card">
              <h3>Schema check (offline)</h3>
              <p className="hint">Validate a JSON reply against <code>{String(agent.output_schema.title)}</code>, the schema ADK enforces on this agent's output.</p>
              <div className="cols">
                <pre className="schema">{JSON.stringify(agent.output_schema, null, 2)}</pre>
                <div>
                  <textarea value={raw} onChange={e => setRaw(e.target.value)} rows={3} />
                  <button onClick={() => validateOutput(agent.id!, raw).then(setVres)}>Validate</button>
                  {vres !== null && <pre className={(vres as { valid: boolean }).valid ? 'okbox' : 'badbox'}>{JSON.stringify(vres, null, 2)}</pre>}
                </div>
              </div>
            </section>
          )}

          {agent.id === 'llm_auditor' && (
            <section className="card">
              <h3>Reviser callback (offline)</h3>
              <p className="hint">Runs the real <code>_remove_end_of_edit_mark</code> after-model callback on text you supply. Everything after <code>---END-OF-EDIT---</code> is dropped.</p>
              <textarea value={cbText} onChange={e => setCbText(e.target.value)} rows={4} />
              <button onClick={() => reviserCallback(cbText).then(setCbRes)}>Apply callback</button>
              {cbRes && <pre className="okbox">{cbRes.output}</pre>}
            </section>
          )}
        </main>}
      </div>
    </div>
  )
}
