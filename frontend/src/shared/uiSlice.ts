import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export type SnackbarSeverity = 'success' | 'info' | 'warning' | 'error'

type UiState = {
  snackbar: {
    open: boolean
    message: string
    severity: SnackbarSeverity
  }
  globalBusy: boolean
  sideNavOpen: boolean
}

const initialState: UiState = {
  snackbar: { open: false, message: '', severity: 'info' },
  globalBusy: false,
  sideNavOpen: true,
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    showSnackbar(
      state,
      action: PayloadAction<{ message: string; severity?: SnackbarSeverity }>,
    ) {
      state.snackbar = {
        open: true,
        message: action.payload.message,
        severity: action.payload.severity ?? 'info',
      }
    },
    hideSnackbar(state) {
      state.snackbar.open = false
    },
    setGlobalBusy(state, action: PayloadAction<boolean>) {
      state.globalBusy = action.payload
    },
    setSideNavOpen(state, action: PayloadAction<boolean>) {
      state.sideNavOpen = action.payload
    },
    toggleSideNav(state) {
      state.sideNavOpen = !state.sideNavOpen
    },
  },
})

export const { showSnackbar, hideSnackbar, setGlobalBusy, setSideNavOpen, toggleSideNav } =
  uiSlice.actions
export default uiSlice.reducer
