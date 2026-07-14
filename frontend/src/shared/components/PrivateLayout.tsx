import { Box, Snackbar, Alert, useMediaQuery } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import { Outlet } from 'react-router-dom'
import { AppBar } from '@/shared/components/AppBar'
import { SideNav, sideNavWidth } from '@/shared/components/SideNav'
import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { hideSnackbar } from '@/shared/uiSlice'

export function PrivateLayout() {
  const theme = useTheme()
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'))
  const sideNavOpen = useAppSelector((s) => s.ui.sideNavOpen)
  const snackbar = useAppSelector((s) => s.ui.snackbar)
  const dispatch = useAppDispatch()

  const contentMargin =
    isDesktop && sideNavOpen ? `${sideNavWidth}px` : 0

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar />
      <Box sx={{ display: 'flex', flex: 1 }}>
        <SideNav />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: { xs: 2, md: 3 },
            ml: contentMargin,
            transition: theme.transitions.create('margin', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
            maxWidth: '100%',
          }}
        >
          <Outlet />
        </Box>
      </Box>
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => dispatch(hideSnackbar())}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        sx={{ zIndex: (t) => t.zIndex.modal + 1 }}
      >
        <Alert
          onClose={() => dispatch(hideSnackbar())}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
