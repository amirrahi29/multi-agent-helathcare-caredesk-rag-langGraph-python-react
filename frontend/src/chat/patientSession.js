import { PATIENT_PROFILE_KEY } from './constants'
import { INTRO_SESSION_KEY } from './agentFlowExplain'

export function readStoredPatientProfile() {
  try {
    const raw = localStorage.getItem(PATIENT_PROFILE_KEY)
    if (!raw) return null
    const p = JSON.parse(raw)
    if (!p || typeof p.email !== 'string' || !p.email.trim() || typeof p.patient_id !== 'number') return null
    return p
  } catch {
    return null
  }
}

export function introInitiallyHidden() {
  try {
    return sessionStorage.getItem(INTRO_SESSION_KEY) === '1'
  } catch {
    return false
  }
}

/** Intro until we have a verified patient profile in localStorage. */
export function computeInitialShowIntro() {
  if (!readStoredPatientProfile()) return true
  return !introInitiallyHidden()
}
