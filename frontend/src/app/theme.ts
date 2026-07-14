import { createTheme } from '@mui/material/styles'

/**
 * Enterprise clinical-commercial theme for HCP CRM.
 * Teal + slate palette; restrained density for long-form notes.
 */
export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#0F6E6A',
      light: '#3A9591',
      dark: '#0A4F4C',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#2C3E50',
      light: '#54738A',
      dark: '#1A252F',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F3F5F7',
      paper: '#FFFFFF',
    },
    success: { main: '#2E7D57' },
    warning: { main: '#C47B16' },
    error: { main: '#C62828' },
    info: { main: '#1B6CA8' },
    text: {
      primary: '#1B2430',
      secondary: '#5A6A7A',
    },
    divider: 'rgba(27, 36, 48, 0.12)',
  },
  typography: {
    fontFamily: '"Source Sans 3", "Segoe UI", sans-serif',
    h1: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600 },
    h2: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600 },
    h3: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600 },
    h4: { fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600, fontSize: '1.5rem' },
    h5: { fontWeight: 600, fontSize: '1.25rem' },
    h6: { fontWeight: 600, fontSize: '1.05rem' },
    button: { textTransform: 'none', fontWeight: 600 },
    body1: { fontSize: '0.975rem', lineHeight: 1.55 },
    body2: { fontSize: '0.875rem', lineHeight: 1.5 },
  },
  shape: { borderRadius: 8 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundImage:
            'radial-gradient(ellipse at top left, rgba(15, 110, 106, 0.06), transparent 45%), radial-gradient(ellipse at bottom right, rgba(44, 62, 80, 0.05), transparent 40%)',
          backgroundAttachment: 'fixed',
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { borderRadius: 8 },
      },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          border: '1px solid rgba(27, 36, 48, 0.08)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFFFFF',
          color: '#1B2430',
          borderBottom: '1px solid rgba(27, 36, 48, 0.1)',
          boxShadow: 'none',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: '1px solid rgba(27, 36, 48, 0.1)',
          backgroundColor: '#FAFBFC',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            fontWeight: 700,
            backgroundColor: '#EEF2F4',
          },
        },
      },
    },
  },
})
