export type AuthUser = {
  id: string
  name: string
  email: string
  role: 'mr' | 'admin'
}

export type Hcp = {
  id: string
  name: string
  specialty: string
  institution: string
  city: string
}

export type Channel = 'in_person' | 'virtual' | 'phone'

export type Sentiment = 'positive' | 'neutral' | 'negative'

export type ProductRef = {
  id: string
  name: string
}

export type FollowUp = {
  id: string
  text: string
  dueDate?: string
}

export type Interaction = {
  id: string
  hcpId: string
  hcpName: string
  visitAt: string
  channel: Channel
  notes: string
  summary: string
  sentiment: Sentiment
  sentimentScore: number
  products: ProductRef[]
  topics: string[]
  followUps: FollowUp[]
  createdAt: string
}

export type DashboardSummary = {
  interactionsThisWeek: number
  openFollowUps: number
  recentInteractions: Interaction[]
  pendingFollowUps: Array<{
    id: string
    text: string
    hcpName: string
    interactionId: string
    dueDate?: string
  }>
}

export type AiAssistantResult = {
  summary: string
  sentiment: Sentiment
  sentimentScore: number
  products: ProductRef[]
  topics: string[]
  followUps: FollowUp[]
  historySummary: string
  errors: string[]
}
