import { Box, Container, Paper, Typography } from '@mui/material'
import { Outlet } from 'react-router-dom'

export function PublicLayout() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        px: 2,
        background:
          'linear-gradient(160deg, #E8F3F2 0%, #F3F5F7 42%, #E6EBF0 100%)',
      }}
    >
      <Container maxWidth="sm">
        <Typography
          variant="h3"
          align="center"
          sx={{
            mb: 1,
            color: 'primary.main',
            fontFamily: '"Fraunces", Georgia, serif',
          }}
        >
          HCP CRM
        </Typography>
        <Typography align="center" color="text.secondary" sx={{ mb: 3 }}>
          AI-assisted interaction logging for medical representatives
        </Typography>
        <Paper sx={{ p: { xs: 3, sm: 4 } }}>
          <Outlet />
        </Paper>
      </Container>
    </Box>
  )
}
