import { useEffect, useMemo, useState } from 'react'
import { ANSWER_EXTRA_DELAY_MS, FIRST_STEP_DELAY_MS, STEP_REVEAL_MS } from '../constants'

const STEPS_EXCLUDE_FINAL = (trace) =>
  Array.isArray(trace) ? trace.filter((s) => s?.id && s.id !== 'response_agent') : []

/** When the API omits `pipeline_trace`, still show an ordered run for UX. */
function buildSyntheticPipelineSteps(routeMeta) {
  if (!routeMeta || routeMeta === 'Error') return []
  const isTool = /Structured|Tool/.test(String(routeMeta))
  const execId = isTool ? 'tool_agent' : 'rag_agent'
  const execLabel = isTool ? 'Structured retrieval' : 'Knowledge retrieval'
  return [
    { id: 'prepare', label: 'Normalize input', summary: 'Input normalized and ready for routing.' },
    { id: 'query_agent', label: 'Intent classification', summary: 'Question type identified for routing.' },
    {
      id: 'decision_agent',
      label: 'Routing',
      summary: isTool
        ? 'Using structured records for authoritative lookups.'
        : 'Using the knowledge index for contextual retrieval.',
    },
    {
      id: execId,
      label: execLabel,
      summary: isTool
        ? 'Retrieved patient, order, payment, or catalog records as applicable.'
        : 'Retrieved the most relevant passages from ingested documents.',
    },
  ]
}

export function useAssistantPipeline(pipelineTrace, fallbackRouteMeta, onPipelineTick) {
  const stepsBeforeAnswer = useMemo(() => {
    const fromApi = STEPS_EXCLUDE_FINAL(pipelineTrace)
    if (fromApi.length > 0) return fromApi
    return buildSyntheticPipelineSteps(fallbackRouteMeta)
  }, [pipelineTrace, fallbackRouteMeta])
  const skipPipeline = stepsBeforeAnswer.length === 0
  const [revealed, setRevealed] = useState(0)
  const [answerVisible, setAnswerVisible] = useState(skipPipeline)

  useEffect(() => {
    if (skipPipeline) {
      setRevealed(0)
      setAnswerVisible(true)
      return undefined
    }
    const timers = []
    const schedule = (fn, ms) => {
      timers.push(setTimeout(fn, ms))
    }
    setRevealed(0)
    setAnswerVisible(false)
    const instant =
      typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (instant) {
      setRevealed(stepsBeforeAnswer.length)
      setAnswerVisible(true)
      return () => timers.forEach(clearTimeout)
    }
    for (let i = 0; i < stepsBeforeAnswer.length; i += 1) {
      const idx = i
      schedule(() => setRevealed(idx + 1), FIRST_STEP_DELAY_MS + idx * STEP_REVEAL_MS)
    }
    schedule(
      () => setAnswerVisible(true),
      FIRST_STEP_DELAY_MS + stepsBeforeAnswer.length * STEP_REVEAL_MS + ANSWER_EXTRA_DELAY_MS,
    )
    return () => timers.forEach(clearTimeout)
  }, [skipPipeline, pipelineTrace, fallbackRouteMeta, stepsBeforeAnswer.length])

  useEffect(() => {
    onPipelineTick?.()
  }, [revealed, answerVisible, onPipelineTick])

  const visibleSteps = stepsBeforeAnswer.slice(0, revealed)

  return { visibleSteps, answerVisible, skipPipeline }
}
