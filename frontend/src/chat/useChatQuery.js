import { useCallback, useState } from 'react'
import { API_BASE, SESSION_STORAGE_KEY } from './constants'
import { isDigitOnly, randomId } from './utils'

/**
 * Sends user text to `/query`, appends user + assistant messages, keeps session + follow-up context.
 */
export function useChatQuery(sessionId, setSessionId, patientEmail) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [lastContextQuery, setLastContextQuery] = useState(null)

  const sendQuery = useCallback(
    async (rawInput) => {
      const raw = rawInput.trim()
      if (!raw || loading) return

      setLoading(true)

      const userMsg = { id: randomId(), role: 'user', content: raw }
      setMessages((m) => [...m, userMsg])

      const lastQuery = isDigitOnly(raw) ? lastContextQuery : null
      const body = {
        query: raw,
        last_query: lastQuery,
        session_id: sessionId,
        patient_email: patientEmail,
      }

      try {
        const res = await fetch(`${API_BASE}/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })

        const rawText = await res.text()
        if (!res.ok) {
          let errMsg = `Request failed (${res.status})`
          try {
            const errBody = JSON.parse(rawText)
            const d = errBody.detail
            if (typeof d === 'string') errMsg = d
            else if (Array.isArray(d) && d.length && d[0]?.msg) errMsg = d.map((x) => x.msg).join(' ')
          } catch {
            if (rawText) errMsg = rawText
          }
          throw new Error(errMsg)
        }

        const data = JSON.parse(rawText)
        const routeLabel = data.route === 'tool' ? 'Your records' : 'Health information'

        if (data.session_id && data.session_id !== sessionId) {
          setSessionId(data.session_id)
          try {
            localStorage.setItem(SESSION_STORAGE_KEY, data.session_id)
          } catch {
            /* ignore */
          }
        }

        setMessages((m) => [
          ...m,
          {
            id: randomId(),
            role: 'assistant',
            content: data.response ?? '',
            meta: routeLabel,
            pipelineTrace: Array.isArray(data.pipeline_trace) ? data.pipeline_trace : [],
          },
        ])

        if (!isDigitOnly(raw)) {
          setLastContextQuery(raw)
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Something went wrong'
        setMessages((m) => [
          ...m,
          {
            id: randomId(),
            role: 'assistant',
            content: `Sorry — we could not get an answer: ${msg}. Check your internet connection and try again. If it keeps happening, ask your clinic for help.`,
            meta: 'Problem',
          },
        ])
      } finally {
        setLoading(false)
      }
    },
    [loading, lastContextQuery, sessionId, setSessionId, patientEmail],
  )

  return {
    messages,
    setMessages,
    loading,
    sendQuery,
    lastContextQuery,
    setLastContextQuery,
  }
}
