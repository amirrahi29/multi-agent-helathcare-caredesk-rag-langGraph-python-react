import React from 'react'
import pipelineDiagram from '../assets/pipeline-diagram.jpg'
import { AssistantTurnBlock } from './AssistantTurnBlock'
import { ChatPipelineLegend } from './AssistantParts'
import { AssistantTypingRow, UserMessageRow } from './MessageRows'
import { MicIcon, SendIcon } from './icons'
import { CHAT_STARTER_CHIPS } from './chatConfig'
import { UI_COPY } from './uiCopy'
import { BRAND_NAME } from './constants'

export function ChatWorkspace({
  displayName,
  greetingTitle,
  messages,
  loading,
  input,
  setInput,
  onComposerKeyDown,
  onSend,
  speechSupported,
  listening,
  toggleListening,
  messagesEndRef,
  scrollToBottom,
}) {
  const trimmedName = displayName.trim()
  const senderLabel = trimmedName || UI_COPY.defaultYou
  const isEmpty = messages.length === 0 && !loading

  return (
    <div className="app-shell app-shell--chat">
      <div className="chat-panel chat-panel--unified" aria-label={UI_COPY.chatAriaLabel}>
        <div className="chat-panel-toolbar">
          <div className="chat-toolbar-left">
            <ChatPipelineLegend />
          </div>
          <div className="chat-toolbar-right">
            {trimmedName ? (
              <span
                className="chat-user-greeting"
                title={greetingTitle}
                aria-label={`${UI_COPY.toolbarSignedIn}: ${trimmedName}`}
              >
                <span className="chat-user-greeting-hi">{UI_COPY.toolbarSignedIn}</span>
                <span className="chat-user-greeting-name">{trimmedName}</span>
              </span>
            ) : null}
            <span className="badge-live" title={UI_COPY.toolbarReadyTitle}>
              <span className="toolbar-pulse" />
              {UI_COPY.toolbarReady}
            </span>
            <span className="badge-soft">{UI_COPY.toolbarMessages(messages.length)}</span>
          </div>
        </div>

        <div className={`messages messages--chat${isEmpty ? ' messages--chat--empty' : ''}`}>
          <div className="chat-messages-inner">
            {isEmpty ? (
              <div className="empty-state-flow-only">
                <div className="empty-state-diagram">
                  <img
                    className="empty-state-flow-img"
                    src={pipelineDiagram}
                    width={1024}
                    height={444}
                    decoding="sync"
                    fetchPriority="high"
                    loading="eager"
                    alt={UI_COPY.emptyDiagramAlt}
                  />
                </div>
                <div className="empty-state-callout">
                  <p className="empty-state-callout-title">{UI_COPY.emptyTitle}</p>
                  <p className="empty-state-callout-sub">{UI_COPY.emptySubtitle}</p>
                  <div className="empty-state-chips" role="group" aria-label={UI_COPY.emptyChipsGroup}>
                    {CHAT_STARTER_CHIPS.map((c) => (
                      <button
                        key={c.label}
                        type="button"
                        className="empty-chip"
                        disabled={loading}
                        onClick={() => setInput(c.text)}
                      >
                        {c.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}

            {messages.map((msg, i) =>
              msg.role === 'user' ? (
                <UserMessageRow key={msg.id ?? `u-${i}`} content={msg.content} senderLabel={senderLabel} />
              ) : (
                <AssistantTurnBlock key={msg.id ?? `a-${i}`} assistantName={BRAND_NAME} msg={msg} onPipelineTick={scrollToBottom} />
              ),
            )}

            {loading ? <AssistantTypingRow assistantName={BRAND_NAME} /> : null}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="composer-wrap">
          <div className="composer-inner">
            <div className="composer">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onComposerKeyDown}
                placeholder={UI_COPY.composerPlaceholder}
                disabled={loading}
                rows={1}
                aria-label={UI_COPY.composerAriaQuestion}
              />
              <div className="composer-footer">
                <span className="composer-footer-hint" aria-hidden>
                  <kbd className="composer-kbd">Enter</kbd> send · <kbd className="composer-kbd">Shift</kbd>+
                  <kbd className="composer-kbd">Enter</kbd> line break
                </span>
                <div className="composer-actions">
                  {speechSupported ? (
                    <button
                      type="button"
                      className={`icon-btn icon-btn--composer ${listening ? 'recording' : ''}`}
                      onClick={toggleListening}
                      disabled={loading}
                      title={listening ? UI_COPY.micStopTitle : UI_COPY.micStartTitle}
                      aria-label={listening ? UI_COPY.micStopAria : UI_COPY.micStartAria}
                    >
                      <MicIcon />
                    </button>
                  ) : null}
                  <button
                    type="button"
                    className="composer-send"
                    onClick={onSend}
                    disabled={loading || !input.trim()}
                    aria-label={UI_COPY.sendAria}
                  >
                    <SendIcon />
                    {UI_COPY.sendLabel}
                  </button>
                </div>
              </div>
            </div>
            <p className="composer-hint">{UI_COPY.composerDisclaimer}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
