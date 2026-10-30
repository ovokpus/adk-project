export type AgentInfo = {
  id?: string; title?: string; example?: string
  name: string; type: string; description: string; model?: string; instruction?: string
  tools?: string[]; output_schema?: Record<string, unknown> | null
  disallow_transfer_to_parent?: boolean; disallow_transfer_to_peers?: boolean
  callbacks?: { before_model: string | null; after_model: string | null }
  sub_agents: AgentInfo[]
}
export type Health = { status: string; model: string; llm: { configured: boolean; backend: string | null; reason: string | null; project?: string } }
export type RunEvent = { author: string; final: boolean; parts: { kind: string; text?: string; name?: string; args?: unknown }[] }
export type RunResult = { run_id: string; backend: string; model: string; elapsed_ms: number; events: RunEvent[] }
export type RunError = { status: number; configured?: boolean; reason: string; note?: string; error?: string }

export const getHealth = (): Promise<Health> => fetch('/health').then(r => r.json())
export const getAgents = (): Promise<AgentInfo[]> => fetch('/api/agents').then(r => r.json())
const post = (url: string, body: unknown) =>
  fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export async function runAgent(id: string, message: string): Promise<RunResult> {
  const r = await post(`/api/agents/${id}/run`, { message })
  const j = await r.json()
  if (!r.ok) throw { status: r.status, ...(typeof j.detail === 'object' ? j.detail : { reason: String(j.detail) }) } as RunError
  return j
}
export const validateOutput = (id: string, raw: string) => post(`/api/agents/${id}/validate-output`, { raw }).then(r => r.json())
export const reviserCallback = (text: string) => post('/api/callbacks/reviser-end-of-edit', { text }).then(r => r.json())
