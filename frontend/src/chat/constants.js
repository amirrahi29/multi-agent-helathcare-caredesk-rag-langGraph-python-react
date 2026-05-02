export const API_BASE = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export const SESSION_STORAGE_KEY = 'multi-agent-session-id'

/** Verified patient from `/verify-patient` (localStorage JSON). */
export const PATIENT_PROFILE_KEY = 'caredesk-patient-profile'

/** Product name — use for headings and assistant identity (keep in sync with tests). */
export const BRAND_NAME = 'CareDesk'

export const STEP_REVEAL_MS = 480
export const FIRST_STEP_DELAY_MS = 350
export const ANSWER_EXTRA_DELAY_MS = 320

export const CHAT_FLOW_STEPS = [
  { key: 'prepare', label: 'Prepare', agentId: 'prepare' },
  { key: 'query', label: 'Question', agentId: 'query_agent' },
  { key: 'decision', label: 'Choose', agentId: 'decision_agent' },
  { key: 'exec', label: 'Look up', agentId: 'tool_agent' },
  { key: 'response', label: 'Answer', agentId: 'response_agent' },
]
