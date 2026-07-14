import type {
  AiAssistantResult,
  AuthUser,
  DashboardSummary,
  Hcp,
  Interaction,
  ProductRef,
} from '@/shared/types'

export const MOCK_USER: AuthUser = {
  id: 'user-1',
  name: 'Priya Sharma',
  email: 'priya.sharma@example.com',
  role: 'mr',
}

export const MOCK_HCPS: Hcp[] = [
  {
    id: 'hcp-1',
    name: 'Dr. Ananya Mehta',
    specialty: 'Cardiology',
    institution: 'Apollo Hospitals',
    city: 'Mumbai',
  },
  {
    id: 'hcp-2',
    name: 'Dr. Rohan Kapoor',
    specialty: 'Oncology',
    institution: 'Tata Memorial',
    city: 'Mumbai',
  },
  {
    id: 'hcp-3',
    name: 'Dr. Kavita Nair',
    specialty: 'Endocrinology',
    institution: 'AIIMS',
    city: 'Delhi',
  },
  {
    id: 'hcp-4',
    name: 'Dr. Imran Qureshi',
    specialty: 'Neurology',
    institution: 'Fortis Escorts',
    city: 'Delhi',
  },
  {
    id: 'hcp-5',
    name: 'Dr. Sneha Reddy',
    specialty: 'Dermatology',
    institution: 'Manipal Hospital',
    city: 'Bengaluru',
  },
  {
    id: 'hcp-6',
    name: 'Dr. Arjun Desai',
    specialty: 'Cardiology',
    institution: 'Narayana Health',
    city: 'Bengaluru',
  },
]

export const MOCK_PRODUCTS: ProductRef[] = [
  { id: 'prod-1', name: 'CardioFlex XR' },
  { id: 'prod-2', name: 'OncoClear 200' },
  { id: 'prod-3', name: 'EndoBalance Plus' },
  { id: 'prod-4', name: 'NeuroCalm SR' },
  { id: 'prod-5', name: 'DermaHeal Ultra' },
]

export const MOCK_INTERACTIONS: Interaction[] = [
  {
    id: 'ix-1',
    hcpId: 'hcp-1',
    hcpName: 'Dr. Ananya Mehta',
    visitAt: '2026-07-10T10:30:00',
    channel: 'in_person',
    notes:
      'Discussed CardioFlex XR titration for patients with mild hypertension. Doctor asked about renal dosing and requested sample packs for next clinic day.',
    summary:
      'Positive discussion on CardioFlex XR titration and renal dosing; samples requested.',
    sentiment: 'positive',
    sentimentScore: 0.82,
    products: [MOCK_PRODUCTS[0]],
    topics: ['Hypertension', 'Renal dosing', 'Sample request'],
    followUps: [
      {
        id: 'fu-1',
        text: 'Deliver CardioFlex XR sample packs',
        dueDate: '2026-07-16',
      },
    ],
    createdAt: '2026-07-10T11:00:00',
  },
  {
    id: 'ix-2',
    hcpId: 'hcp-2',
    hcpName: 'Dr. Rohan Kapoor',
    visitAt: '2026-07-08T15:00:00',
    channel: 'virtual',
    notes:
      'Reviewed OncoClear 200 safety profile in combination therapy. HCP remained neutral on switching protocols until more real-world evidence arrives.',
    summary: 'Neutral stance on OncoClear 200 switch pending further RWE.',
    sentiment: 'neutral',
    sentimentScore: 0.48,
    products: [MOCK_PRODUCTS[1]],
    topics: ['Combination therapy', 'Safety profile', 'RWE'],
    followUps: [
      {
        id: 'fu-2',
        text: 'Share latest OncoClear RWE one-pager',
        dueDate: '2026-07-18',
      },
    ],
    createdAt: '2026-07-08T15:40:00',
  },
  {
    id: 'ix-3',
    hcpId: 'hcp-3',
    hcpName: 'Dr. Kavita Nair',
    visitAt: '2026-07-05T09:15:00',
    channel: 'phone',
    notes:
      'Followed up on EndoBalance Plus adherence program. Clinic staff interested in nurse education session.',
    summary: 'Interest in nurse education for EndoBalance Plus adherence.',
    sentiment: 'positive',
    sentimentScore: 0.74,
    products: [MOCK_PRODUCTS[2]],
    topics: ['Adherence', 'Nurse education'],
    followUps: [
      {
        id: 'fu-3',
        text: 'Schedule nurse education webinar',
        dueDate: '2026-07-20',
      },
    ],
    createdAt: '2026-07-05T09:45:00',
  },
]

export const MOCK_DASHBOARD: DashboardSummary = {
  interactionsThisWeek: 3,
  openFollowUps: 3,
  recentInteractions: MOCK_INTERACTIONS,
  pendingFollowUps: MOCK_INTERACTIONS.flatMap((ix) =>
    ix.followUps.map((fu) => ({
      id: fu.id,
      text: fu.text,
      hcpName: ix.hcpName,
      interactionId: ix.id,
      dueDate: fu.dueDate,
    })),
  ),
}

export function buildMockAiResult(notes: string): AiAssistantResult {
  const lower = notes.toLowerCase()
  const products = MOCK_PRODUCTS.filter((p) =>
    lower.includes(p.name.split(' ')[0]!.toLowerCase()),
  )
  const sentiment =
    lower.includes('concern') || lower.includes('issue')
      ? ('negative' as const)
      : lower.includes('interest') || lower.includes('positive') || lower.includes('request')
        ? ('positive' as const)
        : ('neutral' as const)

  return {
    summary:
      notes.trim().length > 0
        ? `AI draft: ${notes.trim().slice(0, 140)}${notes.trim().length > 140 ? '…' : ''}`
        : 'No notes provided for analysis.',
    sentiment,
    sentimentScore: sentiment === 'positive' ? 0.78 : sentiment === 'negative' ? 0.28 : 0.5,
    products: products.length > 0 ? products : [MOCK_PRODUCTS[0]],
    topics: ['Clinical discussion', 'Product inquiry', 'Follow-up planning'],
    followUps: [
      {
        id: `fu-ai-${Date.now()}`,
        text: 'Send requested materials and confirm next visit',
        dueDate: new Date(Date.now() + 5 * 86400000).toISOString().slice(0, 10),
      },
    ],
    historySummary:
      'Prior visits show steady engagement with titration questions and sample interest.',
    errors: [],
  }
}

/** Simulates network latency for local mock services (no backend). */
export function delay<T>(value: T, ms = 400): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), ms)
  })
}
