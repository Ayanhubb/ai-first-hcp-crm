import { Chip, Paper, Stack, Typography } from '@mui/material'

type TopicsListProps = {
  topics: string[]
}

export function TopicsList({ topics }: TopicsListProps) {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        Medical topics
      </Typography>
      {topics.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No topics suggested yet.
        </Typography>
      ) : (
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          {topics.map((t) => (
            <Chip key={t} label={t} size="small" />
          ))}
        </Stack>
      )}
    </Paper>
  )
}
