import { Box, CircularProgress, Stack, Typography } from '@mui/material'

type LoadingStateProps = {
  label?: string
  minHeight?: number | string
}

export function LoadingState({
  label = 'Loading…',
  minHeight = 240,
}: LoadingStateProps) {
  return (
    <Stack
      alignItems="center"
      justifyContent="center"
      spacing={2}
      sx={{ minHeight, width: '100%' }}
      role="status"
      aria-live="polite"
    >
      <CircularProgress size={36} />
      <Typography color="text.secondary">{label}</Typography>
    </Stack>
  )
}

export function InlineLoading() {
  return (
    <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 1 }}>
      <CircularProgress size={18} />
    </Box>
  )
}
