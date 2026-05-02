import React, { useEffect, useState } from 'react'
import {
  AgentGlyph,
  AssistantBotIcon,
  IngestionIcon,
  MemoryIcon,
  ResponseAgentIcon,
} from './icons'
import { pipeAvatarClass } from './utils'
import { AGENT_INTRO_LABELS, FLOW_STAGES } from './agentFlowExplain'
import { verifyPatientEmail } from './verifyPatient'
import { BRAND_NAME } from './constants'
import { UI_COPY } from './uiCopy'

function IngestionVisual() {
  return (
    <div className="flow-intro-visual flow-intro-visual--ingestion" aria-hidden>
      <div className="flow-intro-hero-icon flow-intro-hero-icon--ingest">
        <IngestionIcon className="flow-intro-hero-glyph" />
      </div>
      <div className="flow-intro-mini-labels">
        <span>Records</span>
        <span className="flow-intro-mini-arrow">→</span>
        <span>Short notes</span>
        <span className="flow-intro-mini-arrow">→</span>
        <span>Search ready</span>
      </div>
    </div>
  )
}

function AgentsVisual({ agentIds = [] }) {
  return (
    <div className="flow-intro-visual flow-intro-visual--agents" aria-hidden>
      <div className="flow-intro-agent-grid">
        {agentIds.map((id, i) => (
          <div key={id} className="flow-intro-agent-cell" style={{ '--agent-i': i }}>
            <div className={`flow-intro-agent-tile ${pipeAvatarClass(id)}`} title={id}>
              <AgentGlyph agentId={id} className="flow-intro-agent-tile-icon" />
            </div>
            <span className="flow-intro-agent-name">{AGENT_INTRO_LABELS[id] || id}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ResponseMemoryVisual() {
  return (
    <div className="flow-intro-visual flow-intro-visual--memory" aria-hidden>
      <div className="flow-intro-dual-heroes">
        <div className="flow-intro-hero-icon flow-intro-hero-icon--response">
          <ResponseAgentIcon className="flow-intro-hero-glyph" />
        </div>
        <div className="flow-intro-hero-icon flow-intro-hero-icon--mem">
          <MemoryIcon className="flow-intro-hero-glyph" />
        </div>
      </div>
      <div className="flow-intro-mini-labels flow-intro-mini-labels--center">
        <AssistantBotIcon className="flow-intro-inline-bot" />
        <span>Answer for you</span>
        <span className="flow-intro-plus">+</span>
        <span>This chat’s memory</span>
      </div>
    </div>
  )
}

/**
 * @param {Object} props
 * @param {(profile: { patient_id: number, name: string, email: string, city: string }) => void} props.onContinue
 * @param {string} [props.defaultEmail]
 */
export function AgentFlowIntro({ onContinue, defaultEmail = '' }) {
  const [email, setEmail] = useState(() => defaultEmail.trim())
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setEmail(defaultEmail.trim())
  }, [defaultEmail])

  const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())

  const submit = async () => {
    if (!emailOk || busy) return
    setError('')
    setBusy(true)
    try {
      const profile = await verifyPatientEmail(email)
      onContinue(profile)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'We could not check this email. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flow-intro" aria-label={`${BRAND_NAME} sign-in and simple explainer`}>
      <div className="flow-intro-content">
        <header className="flow-intro-header">
          <p className="flow-intro-brand">{BRAND_NAME}</p>
          <p className="flow-intro-lead">Use the email your hospital or clinic has on file for you.</p>
        </header>

        <div className="flow-intro-surface flow-intro-surface--signin">
          <h3 className="flow-intro-signin-title">Sign in with email</h3>
          <div className="flow-intro-actions">
            <div className="flow-intro-name-row">
              <label htmlFor="flow-intro-email" className="flow-intro-name-label">
                Email
              </label>
              <input
                id="flow-intro-email"
                type="email"
                className="flow-intro-name-input"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  setError('')
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && emailOk && !busy) {
                    e.preventDefault()
                    submit()
                  }
                }}
                placeholder="you@hospital.org"
                autoComplete="email"
                maxLength={120}
                aria-required="true"
                aria-invalid={Boolean(error)}
                aria-describedby={error ? 'flow-intro-email-error' : undefined}
              />
              <button
                type="button"
                className="flow-intro-btn flow-intro-btn--primary flow-intro-btn--row"
                onClick={submit}
                disabled={!emailOk || busy}
                aria-disabled={!emailOk || busy}
              >
                <span className="flow-intro-btn-label">{busy ? 'Checking…' : 'Continue'}</span>
              </button>
            </div>
            {error ? (
              <p id="flow-intro-email-error" className="flow-intro-error" role="alert">
                {error}
              </p>
            ) : null}
            <p className="flow-intro-name-hint">
              If you share this computer, click <strong>Sign out</strong> when you finish.
            </p>
          </div>
        </div>
      </div>

      <section className="flow-intro-explainer" aria-labelledby="intro-pipeline-title">
        <div className="flow-intro-explainer-inner">
          <h3 id="intro-pipeline-title" className="flow-intro-section-heading">
            {UI_COPY.introExplainerHeading}
          </h3>
          <div className="flow-intro-row" role="list">
            {FLOW_STAGES.map((stage, index) => (
              <React.Fragment key={stage.key}>
                {index > 0 ? (
                  <span
                    className="flow-intro-between flow-intro-connector"
                    style={{ '--conn-i': index - 1 }}
                    aria-hidden
                  >
                    <span className="flow-intro-between-line" />
                    <span className="flow-intro-between-arrow">→</span>
                    <span className="flow-intro-between-line" />
                  </span>
                ) : null}
                <article
                  className="flow-intro-col"
                  style={{ '--flow-i': index }}
                  role="listitem"
                  aria-label={`Step ${stage.step}: ${stage.title}`}
                >
                  <span className="flow-intro-step-badge">Step {stage.step}</span>
                  {stage.visual === 'ingestion' ? (
                    <IngestionVisual />
                  ) : stage.visual === 'agents' ? (
                    <AgentsVisual agentIds={stage.agentIds} />
                  ) : (
                    <ResponseMemoryVisual />
                  )}
                  <h3 className="flow-intro-col-title">{stage.title}</h3>
                  <p className="flow-intro-col-sub">{stage.subtitle}</p>
                  <p className="flow-intro-col-body">{stage.body}</p>
                </article>
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
