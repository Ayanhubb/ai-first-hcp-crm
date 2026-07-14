import { Button, Paper, Stack, Typography } from '@mui/material'

type ReviewSaveBarProps = {
  saving?: boolean
  canSave?: boolean
  onSave: () => void
  hint?: string
}

export function ReviewSaveBar({
  saving,
  canSave = true,
  onSave,
  hint = 'Review AI suggestions, then save. Save works without AI.',
}: ReviewSaveBarProps) {
  return (
    <Paper
      sx={{
        p: 2,
        mt: 2,
        position: 'sticky',
        bottom: 0,
        zIndex: 1,
        bgcolor: 'background.paper',
      }}
    >
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={2}
        alignItems={{ xs: 'stretch', sm: 'center' }}
        justifyContent="space-between"
      >
        <Typography variant="body2" color="text.secondary">
          {hint}
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={onSave}
          disabled={!canSave || saving}
        >
          {saving ? 'Saving…' : 'Save interaction'}
        </Button>
      </Stack>
    </Paper>
  )
}
