import React from 'react'
import { AssistantBotIcon, UserFaceIcon } from './icons'
import { ParticipantName } from './ParticipantName'

export function UserMessageRow({ content, senderLabel = 'You' }) {
  const label = senderLabel?.trim() || 'You'
  return (
    <div className="msg-row user msg-row--user-send" aria-label={`Message from ${label}`}>
      <div className="msg-avatar msg-avatar--user" aria-hidden>
        <UserFaceIcon className="msg-avatar-icon" />
      </div>
      <div className="msg-body">
        <div className="message user message--user-send">{content}</div>
      </div>
    </div>
  )
}

export function AssistantTypingRow({ assistantName }) {
  return (
    <div className="loading-turn">
      <div
        className="msg-row assistant msg-row--typing"
        aria-busy="true"
        aria-label={`${assistantName} is thinking`}
      >
        <div className="msg-avatar msg-avatar--assistant" aria-hidden>
          <AssistantBotIcon className="msg-avatar-icon" />
        </div>
        <div className="msg-body">
          <ParticipantName variant="assistant">{assistantName}</ParticipantName>
          <div className="message assistant typing-bubble" aria-busy="true" aria-live="polite">
            <div className="typing-indicator">
              <span />
              <span />
              <span />
            </div>
          </div>
          <div className="meta-row">
            <span className="route-pill rag">Getting your answer…</span>
          </div>
        </div>
      </div>
    </div>
  )
}
