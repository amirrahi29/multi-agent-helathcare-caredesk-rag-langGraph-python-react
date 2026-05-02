import React, { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'
import { AgentFlowIntro } from './chat/AgentFlowIntro'
import { INTRO_SESSION_KEY } from './chat/agentFlowExplain'
import { ChatWorkspace } from './chat/ChatWorkspace'
import { PATIENT_PROFILE_KEY, SESSION_STORAGE_KEY } from './chat/constants'
import { useSpeechToText } from './chat/hooks/useSpeechToText'
import { computeInitialShowIntro, readStoredPatientProfile } from './chat/patientSession'
import { SiteFooter } from './chat/SiteFooter'
import { SiteHeader } from './chat/SiteHeader'
import { UI_COPY } from './chat/uiCopy'
import { useChatQuery } from './chat/useChatQuery'
import { getOrCreateSessionId, randomId } from './chat/utils'

const App = () => {
  const [showIntro, setShowIntro] = useState(computeInitialShowIntro)
  const [patientProfile, setPatientProfile] = useState(() => readStoredPatientProfile())
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState(getOrCreateSessionId)
  const messagesEndRef = useRef(null)

  const patientEmail = patientProfile?.email?.trim() || ''
  const { messages, setMessages, loading, sendQuery, setLastContextQuery } = useChatQuery(
    sessionId,
    setSessionId,
    patientEmail,
  )

  const { speechSupported, listening, toggleListening } = useSpeechToText(setInput)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    const messagesEl = messagesEndRef.current?.closest?.('.messages--chat')
    if (!messagesEl) return
    if (messages.length === 0 && !loading) {
      messagesEl.scrollTop = 0
      return
    }
    scrollToBottom()
  }, [messages, loading, scrollToBottom])

  const dismissIntro = useCallback((profile) => {
    if (!profile?.email || typeof profile.patient_id !== 'number') return
    try {
      sessionStorage.setItem(INTRO_SESSION_KEY, '1')
      localStorage.setItem(PATIENT_PROFILE_KEY, JSON.stringify(profile))
    } catch {
      /* ignore */
    }
    setPatientProfile(profile)
    setShowIntro(false)
  }, [])

  const startNewChat = useCallback(() => {
    const id = randomId()
    try {
      localStorage.setItem(SESSION_STORAGE_KEY, id)
    } catch {
      /* ignore */
    }
    setSessionId(id)
    setMessages([])
    setLastContextQuery(null)
    setInput('')
  }, [setMessages, setLastContextQuery])

  const switchUser = useCallback(() => {
    if (!window.confirm(UI_COPY.signOutConfirm)) return
    const id = randomId()
    try {
      localStorage.removeItem(PATIENT_PROFILE_KEY)
      localStorage.setItem(SESSION_STORAGE_KEY, id)
      sessionStorage.removeItem(INTRO_SESSION_KEY)
    } catch {
      /* ignore */
    }
    setSessionId(id)
    setMessages([])
    setLastContextQuery(null)
    setInput('')
    setPatientProfile(null)
    setShowIntro(true)
  }, [setMessages, setLastContextQuery])

  const submitMessage = useCallback(() => {
    const raw = input.trim()
    if (!raw || loading) return
    setInput('')
    sendQuery(raw)
  }, [input, loading, sendQuery])

  const onComposerKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        submitMessage()
      }
    },
    [submitMessage],
  )

  const displayName = patientProfile?.name || ''
  const greetingTitle = patientProfile ? `${displayName} · ${patientProfile.email}` : ''
  const hasPatientProfile = Boolean(patientProfile)

  return (
    <div className="app">
      <SiteHeader
        showIntro={showIntro}
        hasPatientProfile={hasPatientProfile}
        loading={loading}
        onSignOut={switchUser}
        onNewChat={startNewChat}
      />

      <div className="app-main" id="main-content" tabIndex={-1}>
        {showIntro ? (
          <AgentFlowIntro defaultEmail={patientProfile?.email || ''} onContinue={dismissIntro} />
        ) : (
          <ChatWorkspace
            displayName={displayName}
            greetingTitle={greetingTitle}
            messages={messages}
            loading={loading}
            input={input}
            setInput={setInput}
            onComposerKeyDown={onComposerKeyDown}
            onSend={submitMessage}
            speechSupported={speechSupported}
            listening={listening}
            toggleListening={toggleListening}
            messagesEndRef={messagesEndRef}
            scrollToBottom={scrollToBottom}
          />
        )}
      </div>

      <SiteFooter />
    </div>
  )
}

export default App
