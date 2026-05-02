import React from 'react'

/** Bold sender line above chat bubbles (user / assistant). */
export function ParticipantName({ variant, children }) {
  return <div className={`msg-participant-name msg-participant-name--${variant}`}>{children}</div>
}
