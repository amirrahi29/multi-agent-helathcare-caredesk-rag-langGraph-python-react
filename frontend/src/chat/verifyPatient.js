import { API_BASE } from './constants'

/**
 * Checks Postgres via API: only known patient emails may use the desk.
 * @returns {{ patient_id: number, name: string, email: string, city: string }}
 */
export async function verifyPatientEmail(email) {
  const trimmed = String(email || '').trim()
  const res = await fetch(`${API_BASE}/verify-patient`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: trimmed }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    let msg = null
    const d = data.detail
    if (typeof d === 'string') msg = d
    else if (Array.isArray(d) && d.length && d[0]?.msg) msg = d.map((x) => x.msg).join(' ')
    throw new Error(msg || `Could not verify email (${res.status})`)
  }
  return data
}
