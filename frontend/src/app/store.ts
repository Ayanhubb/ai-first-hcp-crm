import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import dashboardReducer from '@/features/dashboard/dashboardSlice'
import hcpReducer from '@/features/hcp/hcpSlice'
import aiAssistantReducer from '@/features/ai-assistant/aiAssistantSlice'
import historyReducer from '@/features/interactions/historySlice'
import uiReducer from '@/shared/uiSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    dashboard: dashboardReducer,
    hcp: hcpReducer,
    aiAssistant: aiAssistantReducer,
    history: historyReducer,
    ui: uiReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
