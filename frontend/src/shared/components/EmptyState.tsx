import { Alert, AlertTitle, Button, Stack } from '@mui/material'
import type { ReactNode } from 'react'

type ErrorStateProps = {
  title?: string
  message: string
  onRetry?: () => void
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <Alert
      severity="error"
      action={
        onRetry ? (
          <Button color="inherit" size="small" onClick={onRetry}>
            Retry
          </Button>
        ) : undefined
      }
    >
      <AlertTitle>{title}</AlertTitle>
      {message}
    </Alert>
  )
}

type EmptyStateProps = {
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <Stack
      spacing={1.5}
      alignItems="flex-start"
      sx={{
        py: 4,
        px: 2,
        border: '1px dashed',
        borderColor: 'divider',
        borderRadius: 2,
        bgcolor: 'background.paper',
      }}
    >
      <Alert severity="info" sx={{ width: '100%', bgcolor: 'transparent', border: 0, p: 0 }}>
        <AlertTitle sx={{ mb: description ? 0.5 : 0 }}>{title}</AlertTitle>
        {description}
      </Alert>
      {action}
    </Stack>
  )
}
