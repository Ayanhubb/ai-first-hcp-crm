import { useEffect, type ReactNode } from 'react'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { CssBaseline, ThemeProvider } from '@mui/material'
import { store } from '@/app/store'
import { theme } from '@/app/theme'
import { bindAuthFailureHandler, bootstrapSession } from '@/features/auth/authSlice'

bindAuthFailureHandler(store.dispatch)

type AppProvidersProps = {
  children: ReactNode
}

function SessionBootstrap({ children }: { children: ReactNode }) {
  useEffect(() => {
    void store.dispatch(bootstrapSession())
  }, [])
  return children
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <SessionBootstrap>{children}</SessionBootstrap>
        </BrowserRouter>
      </ThemeProvider>
    </Provider>
  )
}
