import React from 'react'
import botLogo from '../assets/bot-logo.svg'
import { UI_COPY } from './uiCopy'

export function SiteHeader({ showIntro, hasPatientProfile, loading, onSignOut, onNewChat }) {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <div className="brand-row">
          <div className="brand">
            <div className="brand-mark" aria-hidden>
              <img src={botLogo} alt="" className="brand-mark-img" width={44} height={44} decoding="async" />
            </div>
            <div className="brand-text">
              <h1>{UI_COPY.brand}</h1>
              <p className="site-header-tagline">{UI_COPY.headerTagline}</p>
            </div>
          </div>
          <div className="header-actions">
            {hasPatientProfile ? (
              <>
                <button type="button" className="btn-header btn-header--ghost" onClick={onSignOut}>
                  {UI_COPY.signOut}
                </button>
                {!showIntro ? (
                  <button type="button" className="btn-header" onClick={onNewChat} disabled={loading}>
                    {UI_COPY.newChat}
                  </button>
                ) : null}
              </>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  )
}
