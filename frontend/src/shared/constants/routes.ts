export const ROUTES = {
  login: '/login',
  dashboard: '/',
  hcps: '/hcps',
  newInteraction: (hcpId: string) => `/hcps/${hcpId}/interactions/new`,
  interactions: '/interactions',
  interactionDetail: (id: string) => `/interactions/${id}`,
} as const
