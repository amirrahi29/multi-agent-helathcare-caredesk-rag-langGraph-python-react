import { useCallback, useEffect, useRef, useState } from 'react'

const RECOGNITION_LANG = 'hi-IN'

/**
 * Browser speech-to-text for the composer (hi-IN). No-op when unsupported.
 */
export function useSpeechToText(setInput) {
  const [speechSupported, setSpeechSupported] = useState(false)
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef(null)

  useEffect(() => {
    const SR = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)
    if (!SR) return
    setSpeechSupported(true)
    const rec = new SR()
    rec.lang = RECOGNITION_LANG
    rec.continuous = false
    rec.interimResults = false

    rec.onresult = (event) => {
      const chunks = []
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        chunks.push(event.results[i][0].transcript)
      }
      const text = chunks.join('').trim()
      if (!text) return
      setInput((prev) => (prev.trim() ? `${prev.trim()} ${text}` : text))
    }

    rec.onerror = () => setListening(false)
    rec.onend = () => setListening(false)

    recognitionRef.current = rec
    return () => {
      try {
        rec.abort()
      } catch {
        /* ignore */
      }
    }
  }, [setInput])

  const toggleListening = useCallback(() => {
    const rec = recognitionRef.current
    if (!rec) return
    if (listening) {
      try {
        rec.stop()
      } catch {
        /* ignore */
      }
      setListening(false)
      return
    }
    try {
      rec.start()
      setListening(true)
    } catch {
      setListening(false)
    }
  }, [listening])

  return { speechSupported, listening, toggleListening }
}
