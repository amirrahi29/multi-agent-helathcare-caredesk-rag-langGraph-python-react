import React from 'react'
import { FinalAnswerRow, PipelineSteps } from './AssistantParts'
import { ParticipantName } from './ParticipantName'
import { useAssistantPipeline } from './hooks/useAssistantPipeline'
import { routePillClass } from './utils'

/**
 * One assistant turn: orchestration steps (staggered) then final answer.
 */
export function AssistantTurnBlock({ msg, onPipelineTick, assistantName }) {
  const { visibleSteps, answerVisible } = useAssistantPipeline(msg.pipelineTrace, msg.meta, onPipelineTick)

  return (
    <div className="assistant-turn">
      <div className="assistant-turn-identity">
        <ParticipantName variant="assistant">{assistantName}</ParticipantName>
      </div>
      <PipelineSteps steps={visibleSteps} />
      {answerVisible ? <FinalAnswerRow content={msg.content} meta={msg.meta} routePillClass={routePillClass} /> : null}
    </div>
  )
}
