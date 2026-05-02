import React from 'react'
import { UI_COPY } from './uiCopy'

export function SiteFooter() {
  const year = new Date().getFullYear()
  return (
    <footer className="site-footer" role="contentinfo">
      <p className="site-footer-line">{UI_COPY.footerLine(year)}</p>
    </footer>
  )
}
