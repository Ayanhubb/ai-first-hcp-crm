import { List, ListItem, ListItemText, Paper, Typography } from '@mui/material'
import type { FollowUp } from '@/shared/types'

type FollowUpSuggestionsProps = {
  followUps: FollowUp[]
}

export function FollowUpSuggestions({ followUps }: FollowUpSuggestionsProps) {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        Follow-up suggestions
      </Typography>
      {followUps.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No follow-ups suggested yet.
        </Typography>
      ) : (
        <List dense disablePadding>
          {followUps.map((fu) => (
            <ListItem key={fu.id} disableGutters>
              <ListItemText
                primary={fu.text}
                secondary={fu.dueDate ? `Due ${fu.dueDate}` : undefined}
              />
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  )
}
