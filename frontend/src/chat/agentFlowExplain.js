/**
 * Short labels for intro grid tiles (full pipeline order).
 */
export const AGENT_INTRO_LABELS = {
  prepare: 'Get ready',
  query_agent: 'Read question',
  decision_agent: 'Pick path',
  tool_agent: 'Your records',
  rag_agent: 'Guides & text',
  response_agent: 'Answer',
}

/**
 * Three high-level stages for the pre-chat overview (row layout).
 */
export const FLOW_STAGES = [
  {
    key: 'ingestion',
    step: 1,
    title: 'Your information is loaded',
    subtitle: 'Safe storage',
    body: 'Your health details that the app may use are kept in a secure system. Important text is also prepared so the app can find the right bits quickly when you ask something.',
    visual: 'ingestion',
  },
  {
    key: 'agents',
    step: 2,
    title: 'The app figures out what you need',
    subtitle: 'Smart steps',
    body: 'First it understands your question. Then it chooses: look up your personal records, or read trusted written information. Both paths are controlled so answers stay relevant.',
    visual: 'agents',
    agentIds: ['prepare', 'query_agent', 'decision_agent', 'tool_agent', 'rag_agent', 'response_agent'],
  },
  {
    key: 'response_memory',
    step: 3,
    title: 'You get a clear reply',
    subtitle: 'Uses this chat too',
    body: 'The reply mixes what was found with short memory from this same chat, so follow-up questions like “what about last time?” still make sense.',
    visual: 'response_memory',
  },
]

export const INTRO_SESSION_KEY = 'multi-agent-intro-dismissed'
