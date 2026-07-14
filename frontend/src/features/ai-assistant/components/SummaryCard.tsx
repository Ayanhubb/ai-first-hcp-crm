import { Paper, Typography } from '@mui/material'

type SummaryCardProps = {
  title: string
  body: string
  emptyText?: string
}

export function SummaryCard({
  title,
  body,
  emptyText = 'Run Analyze to generate this section.',
}: SummaryCardProps) {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
        {body.trim() ? body : emptyText}
      </Typography>
    </Paper>
  )
}
