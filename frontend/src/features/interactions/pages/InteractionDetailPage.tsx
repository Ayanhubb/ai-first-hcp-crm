import {
  Box,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Typography,
} from '@mui/material'
import { useEffect } from 'react'
import { Link as RouterLink, useParams } from 'react-router-dom'
import { Button } from '@mui/material'
import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { fetchInteractionById } from '@/features/interactions/historySlice'
import { SentimentBadge } from '@/features/ai-assistant/components/SentimentBadge'
import { PageHeader } from '@/shared/components/PageHeader'
import { ErrorState } from '@/shared/components/EmptyState'
import { LoadingState } from '@/shared/components/LoadingState'
import { ROUTES } from '@/shared/constants/routes'

export function InteractionDetailPage() {
  const { id = '' } = useParams()
  const dispatch = useAppDispatch()
  const { selected, status, error } = useAppSelector((s) => s.history)

  useEffect(() => {
    if (id) void dispatch(fetchInteractionById(id))
  }, [dispatch, id])

  if (status === 'loading' || status === 'idle') {
    return <LoadingState label="Loading interaction…" />
  }

  if (status === 'failed' || !selected) {
    return (
      <ErrorState
        title="Interaction not found"
        message={error ?? 'Unable to load this record'}
        onRetry={() => void dispatch(fetchInteractionById(id))}
      />
    )
  }

  const ix = selected

  return (
    <Box>
      <PageHeader
        title={ix.hcpName}
        subtitle={`Visit ${new Date(ix.visitAt).toLocaleString()}`}
        actions={
          <Button component={RouterLink} to={ROUTES.interactions} variant="outlined">
            Back to history
          </Button>
        }
      />

      <Paper sx={{ p: 3 }}>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
            <Chip
              label={ix.channel.replace('_', ' ')}
              size="small"
              sx={{ textTransform: 'capitalize' }}
            />
            <SentimentBadge sentiment={ix.sentiment} score={ix.sentimentScore} />
          </Stack>

          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Summary
            </Typography>
            <Typography>{ix.summary}</Typography>
          </Box>

          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Notes
            </Typography>
            <Typography sx={{ whiteSpace: 'pre-wrap' }}>{ix.notes}</Typography>
          </Box>

          <Divider />

          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Products
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {ix.products.map((p) => (
                <Chip key={p.id} label={p.name} color="primary" variant="outlined" />
              ))}
            </Stack>
          </Box>

          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Topics
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {ix.topics.map((t) => (
                <Chip key={t} label={t} size="small" />
              ))}
            </Stack>
          </Box>

          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Follow-ups
            </Typography>
            <List dense disablePadding>
              {ix.followUps.map((fu) => (
                <ListItem key={fu.id} disableGutters>
                  <ListItemText
                    primary={fu.text}
                    secondary={fu.dueDate ? `Due ${fu.dueDate}` : undefined}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        </Stack>
      </Paper>
    </Box>
  )
}
