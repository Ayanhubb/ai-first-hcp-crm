import { Chip } from '@mui/material'
import type { Sentiment } from '@/shared/types'

const colorMap: Record<Sentiment, 'success' | 'default' | 'error'> = {
  positive: 'success',
  neutral: 'default',
  negative: 'error',
}

type SentimentBadgeProps = {
  sentiment: Sentiment | null
  score?: number | null
}

export function SentimentBadge({ sentiment, score }: SentimentBadgeProps) {
  if (!sentiment) {
    return <Chip size="small" label="No sentiment" variant="outlined" />
  }
  const scoreLabel =
    typeof score === 'number' ? ` · ${(score * 100).toFixed(0)}%` : ''
  return (
    <Chip
      size="small"
      color={colorMap[sentiment]}
      label={`${sentiment}${scoreLabel}`}
      sx={{ textTransform: 'capitalize' }}
    />
  )
}
