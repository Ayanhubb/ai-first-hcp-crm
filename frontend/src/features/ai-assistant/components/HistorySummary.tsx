import { Paper, Typography } from '@mui/material'

type HistorySummaryProps = {
  text: string
}

export function HistorySummary({ text }: HistorySummaryProps) {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        History summary
      </Typography>
      <Typography variant="body2">
        {text.trim() || 'History context appears after Analyze.'}
      </Typography>
    </Paper>
  )
}
