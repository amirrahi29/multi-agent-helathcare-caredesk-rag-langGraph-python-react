import { BRAND_NAME } from './constants'

/** Central UI strings for shell + chat (single place to edit copy). */
export const UI_COPY = {
  brand: BRAND_NAME,
  headerTagline:
    'Answers about your care from your own health data. Type or use voice (Chrome or Edge; Hindi supported).',
  signOut: 'Sign out',
  newChat: 'New chat',
  signOutConfirm: 'Sign out? This will clear your name, email, and chat on this device only.',
  introExplainerHeading: 'What happens when you ask',
  toolbarSignedIn: 'Signed in',
  toolbarReady: 'Ready',
  toolbarReadyTitle: 'The service is running',
  toolbarMessages: (n) => `${n} messages`,
  chatAriaLabel: 'Care assistant chat',
  emptyDiagramAlt: `Picture of how ${BRAND_NAME} reads your information and answers your questions.`,
  emptyTitle: 'What would you like to know?',
  emptySubtitle:
    'You can ask in simple words about orders, medicines, your doctor or care team, or payments. Answers use information tied to the email you signed in with.',
  emptyChipsGroup: 'Example questions',
  composerPlaceholder: 'Type your question here…',
  composerAriaQuestion: 'Your question',
  micStopTitle: 'Stop listening',
  micStartTitle: 'Speak instead of typing (Hindi)',
  micStopAria: 'Stop listening',
  micStartAria: 'Speak your question',
  sendAria: 'Send',
  sendLabel: 'Send',
  composerDisclaimer:
    'This chat is saved only in this browser. Do not use it for emergencies. Always follow your clinic’s rules and your doctor’s advice for real medical decisions.',
  defaultYou: 'You',
  footerLine: (year) =>
    `© ${year} ${BRAND_NAME} · Demo — sample data only; not for emergencies or clinical decisions.`,
}
