import { Box, Button, Typography } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'
import { ROUTES } from '@/shared/constants/routes'

export function NotFoundPage() {
  return (
    <Box sx={{ textAlign: 'center', py: 8 }}>
      <Typography variant="h3" gutterBottom>
        Page not found
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        The route you requested does not exist.
      </Typography>
      <Button component={RouterLink} to={ROUTES.dashboard} variant="contained">
        Go to dashboard
      </Button>
    </Box>
  )
}
